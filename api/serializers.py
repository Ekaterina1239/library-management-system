from rest_framework import serializers
from django.contrib.auth import authenticate
from accounts.models import User, StaffInvite
from books.models import Genre, Author, Book
from loans.models import Loan, Reservation
from notifications.models import Notification, NotificationPreference


class UserSerializer(serializers.ModelSerializer):
    user_type_display = serializers.CharField(source='get_user_type_display', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'user_type', 'user_type_display', 'phone_number', 'address',
            'date_of_birth', 'membership_id', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'membership_id', 'created_at']


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone_number', 'address', 'date_of_birth'
        ]

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
        else:
            raise serializers.ValidationError('Must include username and password')

        attrs['user'] = user
        return attrs


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ['id', 'name', 'description']


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ['id', 'first_name', 'last_name', 'bio', 'date_of_birth', 'date_of_death']


class BookSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.__str__', read_only=True)
    genre_name = serializers.CharField(source='genre.name', read_only=True)
    is_available = serializers.BooleanField(read_only=True)

    class Meta:
        model = Book
        fields = [
            'id', 'title', 'author', 'author_name', 'isbn', 'genre', 'genre_name',
            'publication_year', 'publisher', 'description', 'total_copies',
            'available_copies', 'cover_image', 'is_available', 'created_at'
        ]


class LoanSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    book_title = serializers.CharField(source='book.title', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    days_overdue = serializers.IntegerField(read_only=True)
    can_renew = serializers.BooleanField(read_only=True)

    class Meta:
        model = Loan
        fields = [
            'id', 'user', 'user_name', 'book', 'book_title', 'borrowed_date',
            'due_date', 'returned_date', 'status', 'renewals', 'max_renewals',
            'is_overdue', 'days_overdue', 'can_renew'
        ]
        read_only_fields = ['borrowed_date', 'status', 'renewals']


class ReservationSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    book_title = serializers.CharField(source='book.title', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = Reservation
        fields = [
            'id', 'user', 'user_name', 'book', 'book_title', 'reserved_date',
            'expiry_date', 'status', 'notified', 'priority', 'is_expired'
        ]
        read_only_fields = ['reserved_date', 'priority', 'notified']


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'title', 'message', 'notification_type',
            'is_read', 'created_at', 'related_object_id', 'related_content_type'
        ]
        read_only_fields = ['created_at']


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = [
            'email_due_reminders', 'email_overdue_alerts',
            'email_reservation_available', 'email_general'
        ]
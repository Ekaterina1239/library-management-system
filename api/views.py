from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta

from accounts.models import User
from books.models import Book, Author, Genre
from loans.models import Loan, Reservation
from notifications.models import Notification, NotificationPreference
from .serializers import *


class IsLibrarianOrHigher(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type in ['librarian', 'it_staff', 'management']


class IsReader(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'reader'


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()  # ⬅️ ДОБАВЛЕНО
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsLibrarianOrHigher]

    def get_queryset(self):
        if self.request.user.user_type == 'reader':
            return User.objects.filter(id=self.request.user.id)
        return User.objects.all()


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()  # ⬅️ ДОБАВЛЕНО
    serializer_class = BookSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsLibrarianOrHigher()]
        return [permissions.AllowAny()]

    @action(detail=False, methods=['get'])
    def available(self, request):
        available_books = Book.objects.filter(available_copies__gt=0)
        serializer = self.get_serializer(available_books, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def search(self, request):
        query = request.query_params.get('q', '')
        books = Book.objects.filter(
            Q(title__icontains=query) |
            Q(author__first_name__icontains=query) |
            Q(author__last_name__icontains=query) |
            Q(isbn__icontains=query)
        )
        serializer = self.get_serializer(books, many=True)
        return Response(serializer.data)


class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()  # ⬅️ ДОБАВЛЕНО
    serializer_class = AuthorSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()  # ⬅️ ДОБАВЛЕНО
    serializer_class = GenreSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class LoanViewSet(viewsets.ModelViewSet):
    queryset = Loan.objects.all()  # ⬅️ ДОБАВЛЕНО
    serializer_class = LoanSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'reader':
            return Loan.objects.filter(user=user)
        return Loan.objects.all()

    def perform_create(self, serializer):
        book = serializer.validated_data['book']
        if book.available_copies <= 0:
            raise serializers.ValidationError("Book is not available for loan")

        loan = serializer.save(user=self.request.user)
        return loan

    @action(detail=True, methods=['post'])
    def renew(self, request, pk=None):
        loan = self.get_object()
        if loan.can_renew():
            loan.renewals += 1
            loan.due_date = timezone.now() + timedelta(days=14)
            loan.save()
            serializer = self.get_serializer(loan)
            return Response(serializer.data)
        return Response(
            {'error': 'Cannot renew this loan'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True, methods=['post'])
    def return_book(self, request, pk=None):
        loan = self.get_object()
        loan.returned_date = timezone.now()
        loan.save()
        serializer = self.get_serializer(loan)
        return Response(serializer.data)


class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all()  # ⬅️ ДОБАВЛЕНО
    serializer_class = ReservationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'reader':
            return Reservation.objects.filter(user=user)
        return Reservation.objects.all()

    def perform_create(self, serializer):
        book = serializer.validated_data['book']
        if book.available_copies > 0:
            raise serializers.ValidationError("Book is available, no need to reserve")

        existing_reservation = Reservation.objects.filter(
            user=self.request.user,
            book=book,
            status__in=['pending', 'available']
        ).exists()

        if existing_reservation:
            raise serializers.ValidationError("You already have an active reservation for this book")

        reservation = serializer.save(user=self.request.user)
        return reservation


class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()  # ⬅️ ДОБАВЛЕНО
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def unread(self, request):
        unread_notifications = self.get_queryset().filter(is_read=False)
        serializer = self.get_serializer(unread_notifications, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        serializer = self.get_serializer(notification)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({'status': 'all notifications marked as read'})


class AuthView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            user_serializer = UserSerializer(user)
            return Response({
                'user': user_serializer.data,
                'message': 'Login successful'
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user_serializer = UserSerializer(user)
            return Response({
                'user': user_serializer.data,
                'message': 'Registration successful'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
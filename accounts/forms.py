from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


from django import forms

class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username',
            'autofocus': True
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )

class ReaderRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    phone_number = forms.CharField(required=False)
    address = forms.CharField(widget=forms.Textarea, required=False)
    date_of_birth = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'first_name',
                  'last_name', 'phone_number', 'address', 'date_of_birth')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'reader'  # Все самостоятельные регистрации - читатели
        if commit:
            user.save()
        return user


class UserProfileForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone_number', 'address', 'date_of_birth')


class UserManagementForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'user_type', 'is_active')


# RENAME THIS FORM to avoid conflict with Django's UserCreationForm
class CustomUserCreationForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput,
        required=False,
        help_text="Leave empty to generate random password"
    )
    password2 = forms.CharField(
        label="Password confirmation",
        widget=forms.PasswordInput,
        required=False,
        help_text="Enter the same password as above, for verification."
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'user_type')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user_type'].choices = [
            ('reader', 'Reader'),
            ('librarian', 'Librarian'),
            ('it_staff', 'IT Staff'),
            ('management', 'Management'),
        ]

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")  # ИСПРАВЬТЕ: cleaned_data вместо activated_data

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)

        if not self.cleaned_data["password1"]:
            password = User.objects.make_random_password()
            user.set_password(password)
        else:
            user.set_password(self.cleaned_data["password1"])

        if commit:
            user.save()
        return user

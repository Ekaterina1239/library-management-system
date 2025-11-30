from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from .models import User
from .forms import ReaderRegistrationForm, UserProfileForm, UserManagementForm, CustomUserCreationForm, LoginForm


def is_it_staff(user):
    return user.user_type == 'it_staff'


def is_librarian(user):
    return user.user_type in ['librarian', 'it_staff', 'management']


def is_management(user):
    return user.user_type in ['it_staff', 'management']



def register_view(request):
    if request.user.is_authenticated:
        messages.info(request, 'You are already logged in.')
        return redirect('home')

    if request.method == 'POST':
        form = ReaderRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request,
                             f'Welcome to the library, {user.first_name}! Your reader account has been created.')
            return redirect('home')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ReaderRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


# АВТОРИЗАЦИЯ ДЛЯ ВСЕХ
def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)

            if user is not None:
                if user.is_active:
                    login(request, user)
                    messages.success(request, f'Welcome back, {user.first_name or user.username}!')

                    next_url = request.GET.get('next')
                    if next_url:
                        return redirect(next_url)
                    return redirect('home')
                else:
                    messages.error(request, 'Your account has been deactivated.')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    """Выход из системы"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, 'accounts/profile.html', {'form': form})



@login_required
@user_passes_test(is_it_staff)
def create_staff_user_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            messages.success(request, f'User {user.username} created successfully!')
            return redirect('user_management')
    else:
        form = UserCreationForm()
        # Ограничиваем выбор типов пользователей для IT staff
        form.fields['user_type'].choices = [
            ('reader', 'Reader'),
            ('librarian', 'Librarian'),
            ('it_staff', 'IT Staff'),
            ('management', 'Management')
        ]

    return render(request, 'accounts/create_staff_user.html', {'form': form})


# УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ
@login_required
@user_passes_test(is_librarian)
def user_management_view(request):
    """Управление пользователями для IT staff и выше"""
    users = User.objects.all().order_by('-date_joined')

    # Поиск пользователей
    query = request.GET.get('q')
    if query:
        users = users.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(membership_id__icontains=query)
        )

    # Фильтрация по типу пользователя
    user_type = request.GET.get('user_type')
    if user_type:
        users = users.filter(user_type=user_type)

    return render(request, 'accounts/user_management.html', {
        'users': users,
        'user_types': User.USER_TYPES
    })

@login_required
@user_passes_test(is_it_staff)
def create_staff_user_view(request):
    """IT staff создает пользователей персонала напрямую"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)  # Changed from UserCreationForm to CustomUserCreationForm
        if form.is_valid():
            user = form.save()
            messages.success(request, f'User {user.username} created successfully!')
            return redirect('user_management')
    else:
        form = CustomUserCreationForm()  # Changed from UserCreationForm to CustomUserCreationForm
        # Ограничиваем выбор типов пользователей для IT staff
        form.fields['user_type'].choices = [
            ('reader', 'Reader'),
            ('librarian', 'Librarian'),
            ('it_staff', 'IT Staff'),
            ('management', 'Management')
        ]

    return render(request, 'accounts/create_staff_user.html', {'form': form})
# РЕДАКТИРОВАНИЕ ПОЛЬЗОВАТЕЛЯ
@login_required
@user_passes_test(is_librarian)
def user_edit_view(request, user_id):
    """Редактирование пользователя"""
    user = get_object_or_404(User, id=user_id)

    # IT staff может редактировать только читателей и библиотекарей
    if request.user.user_type == 'it_staff' and user.user_type in ['it_staff', 'management']:
        messages.error(request, 'You do not have permission to edit this user.')
        return redirect('user_management')

    if request.method == 'POST':
        form = UserManagementForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f'User {user.username} updated successfully!')
            return redirect('user_management')
    else:
        form = UserManagementForm(instance=user)
        # Ограничиваем выбор для IT staff
        if request.user.user_type == 'it_staff':
            form.fields['user_type'].choices = [
                ('reader', 'Reader'),
                ('librarian', 'Librarian'),
                ('it_staff', 'IT Staff'),
                ('management', 'Management')

            ]

    return render(request, 'accounts/user_edit.html', {'form': form, 'user': user})


# СБРОС ПАРОЛЯ ПОЛЬЗОВАТЕЛЯ
@login_required
@user_passes_test(is_librarian)
def user_reset_password(request, user_id):
    """Сброс пароля пользователя"""
    user = get_object_or_404(User, id=user_id)

    # IT staff не может сбрасывать пароли других IT staff и management
    if request.user.user_type == 'it_staff' and user.user_type in ['it_staff', 'management']:
        messages.error(request, 'You do not have permission to reset password for this user.')
        return redirect('user_management')

    if request.method == 'POST':
        new_password = User.objects.make_random_password()
        user.set_password(new_password)
        user.save()

        messages.success(request,
                         f'Password for {user.username} has been reset. '
                         f'New password: {new_password}'
                         )
        return redirect('user_management')

    return render(request, 'accounts/user_reset_password.html', {'user': user})


# АКТИВАЦИЯ/ДЕАКТИВАЦИЯ ПОЛЬЗОВАТЕЛЯ
@login_required
@user_passes_test(is_librarian)
def user_toggle_active(request, user_id):
    """Активация/деактивация пользователя"""
    user = get_object_or_404(User, id=user_id)

    # Нельзя деактивировать себя
    if user == request.user:
        messages.error(request, 'You cannot deactivate your own account.')
        return redirect('user_management')

    # IT staff не может управлять другими IT staff и management
    if request.user.user_type == 'it_staff' and user.user_type in ['it_staff', 'management']:
        messages.error(request, 'You do not have permission to modify this user.')
        return redirect('user_management')

    user.is_active = not user.is_active
    user.save()

    action = "activated" if user.is_active else "deactivated"
    messages.success(request, f'User {user.username} has been {action}.')
    return redirect('user_management')


# УДАЛЕНИЕ ПОЛЬЗОВАТЕЛЯ
@login_required
@user_passes_test(is_management)
def user_delete_view(request, user_id):
    """Удаление пользователя (только для management)"""
    user = get_object_or_404(User, id=user_id)

    # Нельзя удалить себя
    if user == request.user:
        messages.error(request, 'You cannot delete your own account.')
        return redirect('user_management')

    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'User {username} has been deleted permanently.')
        return redirect('user_management')

    return render(request, 'accounts/user_confirm_delete.html', {'user': user})


# ПРИНУДИТЕЛЬНЫЙ ВЫХОД (для отладки)
def force_logout_view(request):
    """Принудительный выход из системы"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')


# API ДЛЯ ПРОФИЛЯ
@login_required
def user_profile_api(request):
    """API для получения данных профиля"""
    if request.method == 'GET':
        user = request.user
        return JsonResponse({
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'user_type': user.get_user_type_display(),
            'membership_id': user.membership_id,
            'date_joined': user.date_joined.strftime('%Y-%m-%d')
        })


def clean_password2(self):
    password1 = self.cleaned_data.get("password1")
    password2 = self.cleaned_data.get("password2")

    # Если оба пароля пустые - это нормально (сгенерируется случайный)
    if not password1 and not password2:
        return password2

    # Если один пароль пустой, а другой нет - ошибка
    if password1 and not password2:
        raise forms.ValidationError("Please confirm your password")
    if password2 and not password1:
        raise forms.ValidationError("Please enter your password")

    # Проверка совпадения паролей
    if password1 and password2 and password1 != password2:
        raise forms.ValidationError("Passwords don't match")

    return password2
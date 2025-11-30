from django.urls import path
from . import views
from django.http import HttpResponseRedirect

urlpatterns = [
    # Регистрация и аутентификация
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('force-logout/', views.force_logout_view, name='force_logout'),
    path('profile/', views.profile_view, name='profile'),

    # Управление пользователями (IT staff и выше)
    path('management/', views.user_management_view, name='user_management'),
    path('management/create/', views.create_staff_user_view, name='create_staff_user'),
    path('management/<int:user_id>/edit/', views.user_edit_view, name='user_edit'),
    path('management/<int:user_id>/reset-password/', views.user_reset_password, name='user_reset_password'),
    path('management/<int:user_id>/toggle-active/', views.user_toggle_active, name='user_toggle_active'),
    path('management/<int:user_id>/delete/', views.user_delete_view, name='user_delete'),


    # API
    path('api/profile/', views.user_profile_api, name='user_profile_api'),
]
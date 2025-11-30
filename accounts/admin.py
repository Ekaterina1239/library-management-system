from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_type', 'is_active', 'date_joined')
    list_filter = ('user_type', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'membership_id')
    readonly_fields = ('date_joined', 'last_login', 'membership_id')

    fieldsets = UserAdmin.fieldsets + (
        ('Library Information', {
            'fields': ('user_type', 'phone_number', 'address', 'date_of_birth', 'membership_id')
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Library Information', {
            'fields': ('user_type', 'phone_number', 'address', 'date_of_birth')
        }),
    )
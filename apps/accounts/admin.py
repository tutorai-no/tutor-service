"""
Admin configuration for the accounts app.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, UserProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Admin configuration for the custom User model.
    """
    list_display = ['email', 'first_name', 'last_name', 'is_verified', 'is_active', 'date_joined']
    list_filter = ['is_active', 'is_staff', 'is_superuser', 'is_verified', 'date_joined']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['-date_joined']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'is_verified', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ['date_joined', 'last_login']


class UserProfileInline(admin.StackedInline):
    """
    Inline admin for UserProfile.
    """
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = ['bio', 'timezone', 'language']


UserAdmin.inlines = [UserProfileInline]


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Admin configuration for UserProfile model.
    """
    list_display = ['user', 'timezone', 'language', 'created_at']
    list_filter = ['timezone', 'language', 'created_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (_('User'), {'fields': ('user',)}),
        (_('Profile Information'), {'fields': ('bio', 'timezone', 'language')}),
        (_('Timestamps'), {'fields': ('created_at', 'updated_at')}),
    )
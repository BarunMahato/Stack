from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'name', 'role', 'available_credits', 'is_staff')
    list_filter = ('role', 'is_staff')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Library Info', {'fields': ('name', 'role', 'total_credits_spent')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Library Info', {'fields': ('name', 'role')}),
    )
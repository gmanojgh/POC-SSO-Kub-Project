"""
Django Admin registrations for the Secure Report API.

Provides a full admin UI for managing Roles, Permissions,
RolePermissions, Users, and Reports.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Permission, Report, Role, RolePermission, User


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ["name", "description", "permission_count", "created_at"]
    search_fields = ["name"]
    readonly_fields = ["created_at"]

    @admin.display(description="Permissions")
    def permission_count(self, obj):
        return obj.role_permissions.count()


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ["name", "description"]
    search_fields = ["name"]


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ["role", "permission"]
    list_filter = ["role"]
    search_fields = ["role__name", "permission__name"]


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Extends Django's built-in UserAdmin to expose the role field."""

    list_display = ["username", "email", "role", "is_active", "date_joined"]
    list_filter = ["role", "is_active", "is_staff"]
    search_fields = ["username", "email"]
    ordering = ["username"]

    fieldsets = BaseUserAdmin.fieldsets + (
        ("RBAC", {"fields": ("role",)}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("RBAC", {"fields": ("role",)}),
    )


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ["title", "category", "created_by", "is_active", "created_at"]
    list_filter = ["category", "is_active"]
    search_fields = ["title", "content", "category"]
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["-created_at"]

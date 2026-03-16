"""
Data models for the Secure Report API.

Schema:
    Role          — named role (Admin, Manager, Viewer)
    Permission    — named capability (view_reports, delete_reports …)
    RolePermission— join table: which permissions belong to each role
    User          — extends Django AbstractUser, carries one Role FK
    Report        — the protected resource; soft-deleted via is_active flag
"""

import logging

from django.contrib.auth.models import AbstractUser
from django.db import models

logger = logging.getLogger(__name__)


class Role(models.Model):
    """A named role that groups a set of permissions."""

    name = models.CharField(max_length=50, unique=True, db_index=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Permission(models.Model):
    """A named, granular capability such as view_reports or delete_reports."""

    name = models.CharField(max_length=100, unique=True, db_index=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class RolePermission(models.Model):
    """Many-to-many join between Role and Permission."""

    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name="role_permissions",
    )
    permission = models.ForeignKey(
        Permission,
        on_delete=models.CASCADE,
        related_name="role_permissions",
    )

    class Meta:
        unique_together = ("role", "permission")
        ordering = ["role", "permission"]

    def __str__(self) -> str:
        return f"{self.role.name} → {self.permission.name}"


class User(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.

    Adds a single Role FK.  All RBAC decisions are made via has_permission().
    Always reference via settings.AUTH_USER_MODEL — never import directly
    in third-party code.
    """

    role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
    )

    class Meta(AbstractUser.Meta):
        ordering = ["username"]

    def has_permission(self, permission_name: str) -> bool:
        """
        Return True if this user's role grants the named permission.

        Hits the DB once using the reverse FK through RolePermission.
        Result is not cached here — add Django's cache framework if needed.
        """
        if not self.role_id:
            return False
        return self.role.role_permissions.filter(
            permission__name=permission_name
        ).exists()

    def __str__(self) -> str:
        return f"{self.username} ({self.role or 'no role'})"


class Report(models.Model):
    """
    A report document — the primary protected resource in this system.

    Deletion is soft: is_active=False.  Hard-delete is never performed
    so audit trails remain intact.
    """

    title = models.CharField(max_length=200, db_index=True)
    content = models.TextField()
    category = models.CharField(max_length=100, db_index=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reports",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title

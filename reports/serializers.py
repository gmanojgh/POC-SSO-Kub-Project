"""
Serializers for the Secure Report API.

All serializers use SerializerMethodField for computed/related data so that
null FK values never cause silent field-level failures.
"""

from rest_framework import serializers

from .models import Report, Role, User


class RoleSerializer(serializers.ModelSerializer):
    """Full role representation including its permission list."""

    permissions = serializers.SerializerMethodField()

    class Meta:
        model = Role
        fields = ["id", "name", "description", "permissions"]

    def get_permissions(self, obj: Role) -> list[str]:
        return list(
            obj.role_permissions.values_list("permission__name", flat=True)
        )


class UserSerializer(serializers.ModelSerializer):
    """
    Safe user representation.

    Uses SerializerMethodField for role_name and permissions so the serializer
    never crashes on AnonymousUser or users with no role assigned.
    """

    role_name = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "email", "role_name", "permissions"]

    def get_role_name(self, obj) -> str | None:
        # Guard: obj may be AnonymousUser (health probe) or user with no role
        if not hasattr(obj, "role") or not obj.role:
            return None
        return obj.role.name

    def get_permissions(self, obj) -> list[str]:
        if not hasattr(obj, "role") or not obj.role:
            return []
        return list(
            obj.role.role_permissions.values_list("permission__name", flat=True)
        )


class ReportSerializer(serializers.ModelSerializer):
    """Read serializer — includes denormalised creator username."""

    created_by_username = serializers.CharField(
        source="created_by.username",
        read_only=True,
    )

    class Meta:
        model = Report
        fields = [
            "id",
            "title",
            "content",
            "category",
            "created_by_username",
            "created_at",
            "updated_at",
            "is_active",
        ]
        read_only_fields = ["created_by_username", "created_at", "updated_at", "is_active"]


class ReportCreateSerializer(serializers.ModelSerializer):
    """
    Write serializer for report creation.

    Keeps the input surface minimal — created_by is injected by the view,
    never accepted from the client.
    """

    class Meta:
        model = Report
        fields = ["title", "content", "category"]

    def validate_title(self, value: str) -> str:
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Title must be at least 3 characters.")
        return value.strip()

    def validate_category(self, value: str) -> str:
        return value.strip()

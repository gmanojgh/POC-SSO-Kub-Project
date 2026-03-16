"""
RBAC permission classes for Django REST Framework.

Each class maps directly to a named permission stored in the Permission table.
Add new capabilities by inserting rows — no code changes required.

Usage in a view:
    class MyView(APIView):
        permission_classes = [CanViewReports]
"""

import logging

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


class HasPermission(BasePermission):
    """
    Generic RBAC gate — set `required_permission` on the view class.

    Example:
        class ReportView(APIView):
            permission_classes = [HasPermission]
            required_permission = "view_reports"
    """

    def has_permission(self, request: Request, view: APIView) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        required = getattr(view, "required_permission", None)
        if not required:
            # No specific permission required — authenticated is enough
            return True
        result = request.user.has_permission(required)
        if not result:
            logger.warning(
                "Permission denied: user=%s required=%s",
                request.user.username,
                required,
            )
        return result


class CanViewReports(BasePermission):
    """Grants access to users whose role includes view_reports."""

    def has_permission(self, request: Request, view: APIView) -> bool:
        return (
            request.user.is_authenticated
            and request.user.has_permission("view_reports")
        )


class CanCreateReports(BasePermission):
    """Grants access to users whose role includes create_reports."""

    def has_permission(self, request: Request, view: APIView) -> bool:
        return (
            request.user.is_authenticated
            and request.user.has_permission("create_reports")
        )


class CanDeleteReports(BasePermission):
    """Grants access to users whose role includes delete_reports."""

    def has_permission(self, request: Request, view: APIView) -> bool:
        return (
            request.user.is_authenticated
            and request.user.has_permission("delete_reports")
        )


class CanManageUsers(BasePermission):
    """Grants access to users whose role includes manage_users."""

    def has_permission(self, request: Request, view: APIView) -> bool:
        return (
            request.user.is_authenticated
            and request.user.has_permission("manage_users")
        )

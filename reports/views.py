"""
API views for the Secure Report API.

All views are class-based APIView subclasses.
Permission enforcement is handled by the permission_classes declarations —
views never check credentials directly except ReportDetailView.delete()
which requires a second granular check.
"""

import logging

from django.http import JsonResponse
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Report, User
from .permissions import CanCreateReports, CanDeleteReports, CanManageUsers, CanViewReports
from .serializers import ReportCreateSerializer, ReportSerializer, UserSerializer

logger = logging.getLogger(__name__)


# ─── Health ───────────────────────────────────────────────────────────────────

def health_check(request):
    """
    Kubernetes readiness and liveness probe endpoint.

    Returns HTTP 200 with JSON.  No authentication required.
    Registered at /api/health/ in reports/urls.py.
    """
    return JsonResponse({"status": "ok"})


# ─── Profile ──────────────────────────────────────────────────────────────────

class MeView(APIView):
    """
    GET /api/me/
    Returns the authenticated user's profile, role, and permissions.
    Used by the frontend to determine what UI elements to render.
    """

    def get(self, request: Request) -> Response:
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


# ─── Reports ──────────────────────────────────────────────────────────────────

class ReportListView(APIView):
    """
    GET /api/reports/
    Returns all active reports.  Requires view_reports permission.
    """

    permission_classes = [CanViewReports]

    def get(self, request: Request) -> Response:
        reports = (
            Report.objects
            .filter(is_active=True)
            .select_related("created_by")
            .order_by("-created_at")
        )
        serializer = ReportSerializer(reports, many=True)
        return Response({
            "count": reports.count(),
            "results": serializer.data,
        })


class ReportCreateView(APIView):
    """
    POST /api/reports/create/
    Creates a new report.  Requires create_reports permission.
    The created_by field is always set from the authenticated user — never from request data.
    """

    permission_classes = [CanCreateReports]

    def post(self, request: Request) -> Response:
        serializer = ReportCreateSerializer(data=request.data)
        if serializer.is_valid():
            report = serializer.save(created_by=request.user)
            logger.info("Report created: id=%s by user=%s", report.pk, request.user.username)
            return Response(
                ReportSerializer(report).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReportDetailView(APIView):
    """
    GET    /api/reports/<pk>/   — view one report (requires view_reports)
    DELETE /api/reports/<pk>/   — soft-delete a report (requires delete_reports)

    Soft-delete sets is_active=False.  Records are never hard-deleted
    so audit history is preserved.
    """

    permission_classes = [CanViewReports]

    def _get_active_report(self, pk: int) -> Report | None:
        try:
            return Report.objects.select_related("created_by").get(pk=pk, is_active=True)
        except Report.DoesNotExist:
            return None

    def get(self, request: Request, pk: int) -> Response:
        report = self._get_active_report(pk)
        if not report:
            return Response(
                {"error": "Report not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(ReportSerializer(report).data)

    def delete(self, request: Request, pk: int) -> Response:
        # Secondary granular check — view permission is required to reach here,
        # but delete requires a separate, elevated permission.
        if not request.user.has_permission("delete_reports"):
            logger.warning(
                "Delete denied: user=%s attempted to delete report id=%s",
                request.user.username,
                pk,
            )
            return Response(
                {"error": "You do not have permission to delete reports"},
                status=status.HTTP_403_FORBIDDEN,
            )
        report = self._get_active_report(pk)
        if not report:
            return Response(
                {"error": "Report not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        report.is_active = False
        report.save(update_fields=["is_active", "updated_at"])
        logger.info("Report soft-deleted: id=%s by user=%s", pk, request.user.username)
        return Response({"message": f"Report '{report.title}' deleted successfully"})


# ─── Users ────────────────────────────────────────────────────────────────────

class UserListView(APIView):
    """
    GET /api/users/
    Lists all users with their roles and permissions.
    Requires manage_users permission (Admin only).
    """

    permission_classes = [CanManageUsers]

    def get(self, request: Request) -> Response:
        users = User.objects.select_related("role").order_by("username")
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

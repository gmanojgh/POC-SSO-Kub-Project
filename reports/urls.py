"""
URL patterns for the reports application.

All paths are mounted under /api/ by the root URLconf.
Google auth is registered at the root level (config/urls.py) — not here.
"""

from django.urls import path

from . import views

urlpatterns = [
    # ── Health ────────────────────────────────────────────────────────────────
    path("health/", views.health_check, name="health-check"),

    # ── Profile ───────────────────────────────────────────────────────────────
    path("me/", views.MeView.as_view(), name="me"),

    # ── Reports ───────────────────────────────────────────────────────────────
    path("reports/", views.ReportListView.as_view(), name="report-list"),
    path("reports/create/", views.ReportCreateView.as_view(), name="report-create"),
    path("reports/<int:pk>/", views.ReportDetailView.as_view(), name="report-detail"),

    # ── Users ─────────────────────────────────────────────────────────────────
    path("users/", views.UserListView.as_view(), name="user-list"),
]

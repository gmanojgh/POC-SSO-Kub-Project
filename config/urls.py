"""
Root URL configuration for Secure Report API.

Auth endpoints:
    POST /api/auth/login/       — username + password → JWT
    POST /api/auth/refresh/     — refresh token → new access token
    POST /api/auth/google/      — Google ID token → JWT

App endpoints:
    /api/  — see reports/urls.py
    /      — login page (HTML)
"""

from django.contrib import admin
from django.shortcuts import render
from django.urls import include, path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from reports.google_auth import GoogleSignInView


def login_page(request):
    """Serve the HTML login page at the root URL."""
    return render(request, "login.html")


urlpatterns = [
    # ── Frontend ───────────────────────────────────────────────────────────────
    path("", login_page, name="login"),

    # ── Admin ─────────────────────────────────────────────────────────────────
    path("admin/", admin.site.urls),

    # ── Authentication ────────────────────────────────────────────────────────
    path("api/auth/login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/auth/google/", GoogleSignInView.as_view(), name="google_signin"),

    # ── Application API ───────────────────────────────────────────────────────
    path("api/", include("reports.urls")),
]
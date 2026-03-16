"""
Google Sign-In authentication view.

Flow:
    1. Client sends a Google ID token (obtained from Google Sign-In SDK)
    2. This view verifies the token against Google's public keys
    3. User is found or created in PostgreSQL
    4. New users are assigned the Viewer role automatically
    5. Our own JWT token pair is returned — identical to the normal login flow

The Google credentials (CLIENT_ID) must be set in .env / Kubernetes secret.
"""

import logging

from django.conf import settings
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Role, User

logger = logging.getLogger(__name__)


def _get_tokens_for_user(user: User) -> dict:
    """
    Generate a JWT token pair for any User instance.
    Used by both Google Sign-In and can be reused by other OAuth providers.
    """
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


def _build_unique_username(email: str) -> str:
    """
    Derive a username from an email address.
    Appends a numeric suffix if the base username is already taken.
    """
    base = email.split("@")[0]
    username = base
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f"{base}{counter}"
        counter += 1
    return username


class GoogleSignInView(APIView):
    """
    POST /api/auth/google/

    Request body:
        { "id_token": "<Google ID token string>" }

    Success response (200):
        {
            "message": "Google Sign-In successful",
            "is_new_user": true | false,
            "user": {
                "id": 4,
                "email": "user@gmail.com",
                "username": "user",
                "role": "Viewer",
                "permissions": ["view_reports"]
            },
            "access": "<JWT access token>",
            "refresh": "<JWT refresh token>"
        }

    Error responses:
        400 — id_token missing or email not in token
        401 — token invalid, expired, or not issued for this client
        503 — Google verification service unreachable
    """

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        google_token = request.data.get("id_token")

        if not google_token:
            return Response(
                {"error": "id_token is required in the request body"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not settings.GOOGLE_CLIENT_ID:
            logger.error("GOOGLE_CLIENT_ID is not configured")
            return Response(
                {"error": "Google Sign-In is not configured on this server"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # ── Step 1: Verify with Google ─────────────────────────────────────
        try:
            google_info = id_token.verify_oauth2_token(
                google_token,
                google_requests.Request(),
                settings.GOOGLE_CLIENT_ID,
            )
        except ValueError as exc:
            logger.warning("Google token verification failed: %s", exc)
            return Response(
                {"error": "Invalid or expired Google token"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        except Exception as exc:
            logger.error("Google token verification error: %s", exc)
            return Response(
                {"error": "Could not reach Google verification service"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # ── Step 2: Extract claims ─────────────────────────────────────────
        email = google_info.get("email")
        if not email:
            return Response(
                {"error": "Google token does not contain an email address"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not google_info.get("email_verified", False):
            return Response(
                {"error": "Google account email is not verified"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        first_name = google_info.get("given_name", "")
        last_name = google_info.get("family_name", "")

        # ── Step 3: Find or create the user ───────────────────────────────
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": _build_unique_username(email),
                "first_name": first_name,
                "last_name": last_name,
            },
        )

        # ── Step 4: Assign default role for new users ──────────────────────
        if created:
            try:
                viewer_role = Role.objects.get(name="Viewer")
                user.role = viewer_role
                user.save(update_fields=["role"])
                logger.info("New user created via Google Sign-In: %s", email)
            except Role.DoesNotExist:
                logger.warning(
                    "Viewer role not found — new user %s has no role assigned. "
                    "Run: python manage.py seed_data",
                    email,
                )

        # ── Step 5: Issue our JWT ──────────────────────────────────────────
        tokens = _get_tokens_for_user(user)

        permissions = []
        if user.role:
            permissions = list(
                user.role.role_permissions.values_list("permission__name", flat=True)
            )

        return Response({
            "message": "Google Sign-In successful",
            "is_new_user": created,
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "role": user.role.name if user.role else None,
                "permissions": permissions,
            },
            "access": tokens["access"],
            "refresh": tokens["refresh"],
        })

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from .models import User, Role
 
 
def get_tokens_for_user(user):
    """Generate our own JWT tokens for a user — same as normal login"""
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }
 
 
class GoogleSignInView(APIView):
    """
    POST /api/auth/google/
    Body: { "id_token": "google-id-token-from-frontend" }
    Returns: { "access": "...", "refresh": "...", "user": {...} }
    """
    permission_classes = [AllowAny]  # No auth needed — this IS the login
 
    def post(self, request):
        google_token = request.data.get('id_token')
 
        if not google_token:
            return Response(
                {"error": "id_token is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
 
        try:
            # Step 1: Verify the token with Google
            # This calls Google's servers to confirm the token is genuine
            google_info = id_token.verify_oauth2_token(
                google_token,
                google_requests.Request(),
                settings.GOOGLE_CLIENT_ID
            )
 
        except ValueError as e:
            # Token is invalid, expired, or forged
            return Response(
                {"error": f"Invalid Google token: {str(e)}"},
                status=status.HTTP_401_UNAUTHORIZED
            )
 
        # Step 2: Extract user info from the verified token
        email = google_info.get('email')
        first_name = google_info.get('given_name', '')
        last_name = google_info.get('family_name', '')
        google_user_id = google_info.get('sub')  # Google's unique user ID
 
        if not email:
            return Response(
                {"error": "Could not get email from Google token"},
                status=status.HTTP_400_BAD_REQUEST
            )
 
        # Step 3: Find or create the user in PostgreSQL
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': email.split('@')[0],  # Use part before @ as username
                'first_name': first_name,
                'last_name': last_name,
            }
        )
 
        # Step 4: If new user, assign default Viewer role
        if created:
            try:
                viewer_role = Role.objects.get(name='Viewer')
                user.role = viewer_role
                user.save()
            except Role.DoesNotExist:
                pass  # No role assigned if Viewer role doesn't exist yet
 
        # Step 5: Issue our own JWT token
        tokens = get_tokens_for_user(user)
 
        return Response({
            "message": "Google Sign-In successful",
            "is_new_user": created,
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "role": user.role.name if user.role else None,
            },
            "access": tokens['access'],
            "refresh": tokens['refresh'],
        })

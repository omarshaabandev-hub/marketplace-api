from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.users.serializers import (
    CustomTokenObtainPairSerializer,
    PasswordChangeSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    UserRegisterSerializer,
    UserSerializer,
)
from apps.users.throttles import (
    LoginRateThrottle,
    PasswordResetRateThrottle,
    RegisterRateThrottle,
)

User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom JWT login view returning role and email inside payload."""

    serializer_class = CustomTokenObtainPairSerializer
    throttle_classes = (LoginRateThrottle,)


class RegisterView(generics.CreateAPIView):
    """Endpoint for user registration."""

    serializer_class = UserRegisterSerializer
    permission_classes = (permissions.AllowAny,)
    throttle_classes = (RegisterRateThrottle,)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """Endpoint to view and update currently logged-in user profile (/me)."""

    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user


class LogoutView(APIView):
    """Endpoint to invalidate refresh token (Blacklist)."""

    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"error": "Refresh token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            RefreshToken(refresh_token).blacklist()
        except TokenError:
            return Response(
                {"error": "Invalid or expired token."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {"detail": "Successfully logged out."},
            status=status.HTTP_205_RESET_CONTENT,
        )


class PasswordChangeView(generics.GenericAPIView):
    serializer_class = PasswordChangeSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Password changed successfully."})


class PasswordResetRequestView(generics.GenericAPIView):
    serializer_class = PasswordResetRequestSerializer
    permission_classes = (permissions.AllowAny,)
    throttle_classes = (PasswordResetRateThrottle,)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        users = User.objects.filter(email__iexact=email, is_active=True)
        for user in users:
            if not user.has_usable_password():
                continue
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            confirm_url = request.build_absolute_uri(reverse("users:password_reset_confirm"))
            message = (
                "A password reset was requested for your account. If you requested it, "
                "send a POST request to the following endpoint with the UID, token, "
                "new_password, and confirm_password fields:\n\n"
                f"{confirm_url}\n\nUID: {uid}\nToken: {token}\n"
            )
            EmailMessage(
                subject="Password reset",
                body=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email],
            ).send(using="default")

        return Response(
            {"detail": "If an account exists for that email, reset instructions have been sent."}
        )


class PasswordResetConfirmView(generics.GenericAPIView):
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = (permissions.AllowAny,)
    throttle_classes = (PasswordResetRateThrottle,)

    def post(self, request):
        serializer = self.get_serializer(
            data=request.data,
            context={"request": request, "token_generator": default_token_generator},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Password reset successfully."})

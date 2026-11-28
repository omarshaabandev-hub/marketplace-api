from unittest.mock import Mock

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.permissions import IsAdmin, IsCustomer, IsVendor

User = get_user_model()


@pytest.mark.django_db
class TestUserAuthEndpoints:
    def test_register_user_success(self, api_client):
        url = reverse("users:register")
        data = {
            "email": "testuser@example.com",
            "password": "StrongPassword123!",
            "first_name": "Test",
            "last_name": "User",
            "role": "CUSTOMER",
        }
        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["email"] == data["email"]
        assert data["password"] not in response.data

    def test_registration_ignores_admin_role(self, api_client):
        url = reverse("users:register")
        data = {
            "email": "hacker@example.com",
            "password": "StrongPassword123!",
            "role": "ADMIN",
        }
        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["role"] == User.Role.CUSTOMER

    def test_registration_ignores_vendor_role(self, api_client):
        url = reverse("users:register")
        data = {
            "email": "vendor@example.com",
            "password": "StrongPassword123!",
            "role": "VENDOR",
        }

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["role"] == User.Role.CUSTOMER
        assert User.objects.get(email=data["email"]).role == User.Role.CUSTOMER

    def test_registration_rejects_weak_password(self, api_client):
        response = api_client.post(
            reverse("users:register"),
            {"email": "weak-password@example.com", "password": "12345678"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "password" in response.data

    def test_login_success(self, api_client):
        User.objects.create_user(
            email="login@example.com",
            password="StrongPassword123!",
        )
        url = reverse("users:login")
        data = {
            "email": "login@example.com",
            "password": "StrongPassword123!",
        }
        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data

    def test_get_user_profile_authenticated(self, api_client):
        user = User.objects.create_user(
            email="profile@example.com",
            password="StrongPassword123!",
        )
        api_client.force_authenticate(user=user)
        url = reverse("users:profile")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == user.email

    def test_logout_success(self, api_client):
        user = User.objects.create_user(
            email="logoutuser@example.com",
            password="StrongPassword123!",
        )
        refresh = RefreshToken.for_user(user)
        api_client.force_authenticate(user=user)

        url = reverse("users:logout")
        response = api_client.post(url, {"refresh": str(refresh)})

        assert response.status_code == status.HTTP_205_RESET_CONTENT
        assert response.data["detail"] == "Successfully logged out."

    def test_logout_without_refresh_token_fails(self, api_client):
        user = User.objects.create_user(
            email="logoutfail@example.com",
            password="StrongPassword123!",
        )
        api_client.force_authenticate(user=user)

        url = reverse("users:logout")
        response = api_client.post(url, {})

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_is_throttled(self, api_client):
        url = reverse("users:login")
        payload = {"email": "nobody@example.com", "password": "wrong"}

        for _ in range(5):
            assert api_client.post(url, payload).status_code == status.HTTP_401_UNAUTHORIZED

        assert api_client.post(url, payload).status_code == status.HTTP_429_TOO_MANY_REQUESTS

    def test_register_is_throttled(self, api_client):
        url = reverse("users:register")

        for i in range(5):
            response = api_client.post(
                url,
                {"email": f"user{i}@example.com", "password": "StrongPassword123!"},
            )
            assert response.status_code == status.HTTP_201_CREATED

        response = api_client.post(
            url,
            {"email": "user5@example.com", "password": "StrongPassword123!"},
        )
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    def test_register_rejects_email_differing_only_by_case(self, api_client):
        User.objects.create_user(email="dup@example.com", password="StrongPassword123!")

        response = api_client.post(
            reverse("users:register"),
            {"email": "DUP@Example.com", "password": "StrongPassword123!"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_is_case_insensitive_on_email(self, api_client):
        User.objects.create_user(email="case@example.com", password="StrongPassword123!")

        response = api_client.post(
            reverse("users:login"),
            {"email": "CASE@example.com", "password": "StrongPassword123!"},
        )

        assert response.status_code == status.HTTP_200_OK

    def test_logout_with_invalid_token_returns_400(self, api_client):
        user = User.objects.create_user(email="lo@example.com", password="StrongPassword123!")
        api_client.force_authenticate(user=user)

        response = api_client.post(reverse("users:logout"), {"refresh": "not-a-token"})

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_authenticated_user_can_change_password(self, api_client):
        user = User.objects.create_user(
            email="change-password@example.com",
            password="CurrentStrongPassword123!",
        )
        api_client.force_authenticate(user=user)

        response = api_client.post(
            reverse("users:password_change"),
            {
                "old_password": "CurrentStrongPassword123!",
                "new_password": "NewStrongPassword456!",
                "confirm_password": "NewStrongPassword456!",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.check_password("NewStrongPassword456!")
        assert not user.check_password("CurrentStrongPassword123!")

    def test_password_change_rejects_incorrect_current_password(self, api_client):
        user = User.objects.create_user(
            email="wrong-current-password@example.com",
            password="CurrentStrongPassword123!",
        )
        api_client.force_authenticate(user=user)

        response = api_client.post(
            reverse("users:password_change"),
            {
                "old_password": "IncorrectStrongPassword123!",
                "new_password": "NewStrongPassword456!",
                "confirm_password": "NewStrongPassword456!",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        user.refresh_from_db()
        assert user.check_password("CurrentStrongPassword123!")

    @override_settings(
        MAILERS={"default": {"BACKEND": "django.core.mail.backends.locmem.EmailBackend"}}
    )
    def test_password_reset_request_and_confirm(self, api_client):
        user = User.objects.create_user(
            email="reset-password@example.com",
            password="CurrentStrongPassword123!",
        )

        response = api_client.post(
            reverse("users:password_reset"),
            {"email": "RESET-PASSWORD@example.com"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(mail.outbox) == 1
        assert "If an account exists" in response.data["detail"]
        reset_fields = {
            line.split(": ", maxsplit=1)[0]: line.split(": ", maxsplit=1)[1]
            for line in mail.outbox[0].body.splitlines()
            if line.startswith(("UID: ", "Token: "))
        }

        response = api_client.post(
            reverse("users:password_reset_confirm"),
            {
                "uid": reset_fields["UID"],
                "token": reset_fields["Token"],
                "new_password": "ResetStrongPassword789!",
                "confirm_password": "ResetStrongPassword789!",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.check_password("ResetStrongPassword789!")
        assert not user.check_password("CurrentStrongPassword123!")

    @override_settings(
        MAILERS={"default": {"BACKEND": "django.core.mail.backends.locmem.EmailBackend"}}
    )
    def test_password_reset_does_not_disclose_unknown_email(self, api_client):
        response = api_client.post(
            reverse("users:password_reset"),
            {"email": "unknown@example.com"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert "If an account exists" in response.data["detail"]
        assert len(mail.outbox) == 0

    def test_role_permission_classes(self):
        customer = User(email="c@test.com", role=User.Role.CUSTOMER)
        vendor = User(email="v@test.com", role=User.Role.VENDOR)
        admin = User(email="a@test.com", role=User.Role.ADMIN)

        request_mock = Mock()

        # Test Customer Permission
        request_mock.user = customer
        assert IsCustomer().has_permission(request_mock, None) is True
        assert IsVendor().has_permission(request_mock, None) is False

        # Test Vendor Permission
        request_mock.user = vendor
        assert IsVendor().has_permission(request_mock, None) is True
        assert IsCustomer().has_permission(request_mock, None) is False

        # Test Admin Permission
        request_mock.user = admin
        assert IsAdmin().has_permission(request_mock, None) is True

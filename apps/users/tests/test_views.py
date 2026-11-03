from unittest.mock import Mock

import pytest
from django.contrib.auth import get_user_model
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

    def test_prevent_self_register_as_admin(self, api_client):
        url = reverse("users:register")
        data = {
            "email": "hacker@example.com",
            "password": "StrongPassword123!",
            "role": "ADMIN",
        }
        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

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

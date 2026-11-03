import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    def test_create_user_successful(self):
        user = User.objects.create_user(
            email="user@example.com",
            password="Password123!",
            first_name="Omar",
            last_name="Shaaban",
        )
        assert user.email == "user@example.com"
        assert user.check_password("Password123!")
        assert user.role == User.Role.CUSTOMER
        assert user.is_active
        assert not user.is_staff

    def test_create_superuser_successful(self):
        admin_user = User.objects.create_superuser(
            email="admin@example.com",
            password="AdminPassword123!",
        )
        assert admin_user.email == "admin@example.com"
        assert admin_user.role == User.Role.ADMIN
        assert admin_user.is_staff
        assert admin_user.is_superuser

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.vendors.models import Vendor

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def make_user(db):
    def _make_user(email, role=None):
        user = User.objects.create_user(email=email, password="StrongPass123!")
        if role is not None:
            user.role = role
            user.save(update_fields=["role"])
        return user

    return _make_user


@pytest.fixture
def make_vendor(db):
    def _make_vendor(
        owner, store_name="Test Store", slug="test-store", status=Vendor.Status.PENDING
    ):
        return Vendor.objects.create(owner=owner, store_name=store_name, slug=slug, status=status)

    return _make_vendor

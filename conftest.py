import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    """Fixture to provide a Django REST Framework test client."""
    return APIClient()

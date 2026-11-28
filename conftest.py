import pytest
from django.core.cache import cache
from rest_framework.test import APIClient


@pytest.fixture(autouse=True)
def clear_cache():
    """Throttle counters live in the cache; reset them between tests."""
    cache.clear()


@pytest.fixture
def api_client():
    """Fixture to provide a Django REST Framework test client."""
    return APIClient()

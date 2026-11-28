from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


@pytest.mark.django_db
def test_user_model_is_available_in_admin(admin_client):
    email = f"admin-{uuid4().hex}@example.com"
    admin_user = User.objects.create_superuser(
        email=email,
        password="<TEST_PASSWORD>",
    )
    admin_client.force_login(admin_user)

    response = admin_client.get(reverse("admin:users_user_changelist"))

    assert response.status_code == 200
    assert email in response.content.decode()

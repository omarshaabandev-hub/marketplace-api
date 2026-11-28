import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.vendors.models import Vendor

pytestmark = pytest.mark.django_db
User = get_user_model()


def test_authenticated_user_can_apply(api_client, make_user):
    user = make_user("a@test.com")
    api_client.force_authenticate(user)

    response = api_client.post(
        reverse("vendors:apply"),
        {"store_name": "My Store", "description": "Nice"},
    )

    assert response.status_code == 201
    vendor = Vendor.objects.get(owner=user)
    assert vendor.status == Vendor.Status.PENDING
    assert vendor.slug == "my-store"


def test_anonymous_cannot_apply(api_client):
    response = api_client.post(reverse("vendors:apply"), {"store_name": "X Store"})
    assert response.status_code in (401, 403)


def test_user_cannot_apply_twice(api_client, make_user, make_vendor):
    user = make_user("a@test.com")
    make_vendor(user)

    api_client.force_authenticate(user)

    response = api_client.post(reverse("vendors:apply"), {"store_name": "Another"})
    assert response.status_code == 400
    assert Vendor.objects.filter(owner=user).count() == 1


def test_similar_store_name_is_rejected(api_client, make_user, make_vendor):
    make_vendor(make_user("a@test.com"), store_name="My Store", slug="my-store")
    api_client.force_authenticate(make_user("b@test.com"))

    response = api_client.post(reverse("vendors:apply"), {"store_name": "my  STORE"})

    assert response.status_code == 400


def test_arabic_store_name_gets_a_slug(api_client, make_user):
    user = make_user("a@test.com")
    api_client.force_authenticate(user)

    response = api_client.post(reverse("vendors:apply"), {"store_name": "متجر الأمل"})

    assert response.status_code == 201
    assert Vendor.objects.get(owner=user).slug != ""


def test_client_cannot_set_status_on_apply(api_client, make_user):
    user = make_user("a@test.com")
    api_client.force_authenticate(user)

    api_client.post(reverse("vendors:apply"), {"store_name": "Sneaky", "status": "APPROVED"})

    assert Vendor.objects.get(owner=user).status == Vendor.Status.PENDING


def test_owner_can_view_own_store(api_client, make_user, make_vendor):
    user = make_user("a@test.com")
    make_vendor(user)
    api_client.force_authenticate(user)

    response = api_client.get(reverse("vendors:my-store"))

    assert response.status_code == 200
    assert response.data["owner_email"] == "a@test.com"


def test_user_without_store_gets_404(api_client, make_user):
    api_client.force_authenticate(make_user("a@test.com"))
    assert api_client.get(reverse("vendors:my-store")).status_code == 404


def test_owner_cannot_change_status_or_slug(api_client, make_user, make_vendor):
    user = make_user("a@test.com")
    vendor = make_vendor(user)
    api_client.force_authenticate(user)

    api_client.patch(
        reverse("vendors:my-store"),
        {"status": "APPROVED", "slug": "hacked", "description": "new text"},
    )

    vendor.refresh_from_db()
    assert vendor.status == Vendor.Status.PENDING
    assert vendor.slug == "test-store"
    assert vendor.description == "new text"


def test_users_only_see_your_own_store(api_client, make_user, make_vendor):
    make_vendor(make_user("a@test.com"), store_name="A", slug="a")
    other = make_user("b@test.com")
    make_vendor(other, store_name="B", slug="b")
    api_client.force_authenticate(other)

    response = api_client.get(reverse("vendors:my-store"))

    assert response.data["store_name"] == "B"


def test_admin_approves_and_promotes_owner(api_client, make_user, make_vendor):
    admin = make_user("admin@test.com", role=User.Role.ADMIN)
    owner = make_user("a@test.com")
    vendor = make_vendor(owner)
    api_client.force_authenticate(admin)

    response = api_client.post(
        reverse("vendors:admin-review", args=[vendor.pk]), {"action": "approve"}
    )

    assert response.status_code == 200
    vendor.refresh_from_db()
    owner.refresh_from_db()
    assert vendor.status == Vendor.Status.APPROVED
    assert owner.role == User.Role.VENDOR


def test_reject_doesnot_chang_owner_role(api_client, make_user, make_vendor):
    admin = make_user("admin@test.com", role=User.Role.ADMIN)
    owner = make_user("a@test.com")
    original_role = owner.role
    vendor = make_vendor(owner)
    api_client.force_authenticate(admin)

    response = api_client.post(
        reverse("vendors:admin-review", args=[vendor.pk]), {"action": "reject"}
    )

    assert response.status_code == 200
    vendor.refresh_from_db()
    owner.refresh_from_db()
    assert vendor.status == Vendor.Status.REJECTED
    assert owner.role == original_role


def test_non_admin_cannot_review(api_client, make_user, make_vendor):
    owner = make_user("a@test.com")
    vendor = make_vendor(owner)
    api_client.force_authenticate(owner)

    response = api_client.post(
        reverse("vendors:admin-review", args=[vendor.pk]), {"action": "approve"}
    )

    assert response.status_code == 403
    vendor.refresh_from_db()
    assert vendor.status == Vendor.Status.PENDING


def test_double_approval_returns_409(api_client, make_user, make_vendor):
    admin = make_user("admin@test.com", role=User.Role.ADMIN)
    vendor = make_vendor(make_user("a@test.com"))
    api_client.force_authenticate(admin)
    url = reverse("vendors:admin-review", args=[vendor.pk])

    first = api_client.post(url, {"action": "approve"})
    second = api_client.post(url, {"action": "approve"})

    assert first.status_code == 200
    assert second.status_code == 409


def test_review_unknown_vendor_returns_404(api_client, make_user):
    api_client.force_authenticate(make_user("admin@test.com", role=User.Role.ADMIN))
    response = api_client.post(reverse("vendors:admin-review", args=[9999]), {"action": "approve"})
    assert response.status_code == 404


def test_store_name_without_letters_is_rejected(api_client, make_user):
    api_client.force_authenticate(make_user("a@test.com"))

    response = api_client.post(reverse("vendors:apply"), {"store_name": "!!!"})

    assert response.status_code == 400


def test_invalid_action_returns_400(api_client, make_user, make_vendor):
    admin = make_user("admin@test.com", role=User.Role.ADMIN)
    vendor = make_vendor(make_user("a@test.com"))
    api_client.force_authenticate(admin)

    response = api_client.post(
        reverse("vendors:admin-review", args=[vendor.pk]), {"action": "delete"}
    )

    assert response.status_code == 400


def test_cannot_reject_an_approved_vendor(api_client, make_user, make_vendor):
    admin = make_user("admin@test.com", role=User.Role.ADMIN)
    vendor = make_vendor(make_user("a@test.com"), status=Vendor.Status.APPROVED)
    api_client.force_authenticate(admin)

    response = api_client.post(
        reverse("vendors:admin-review", args=[vendor.pk]), {"action": "reject"}
    )

    assert response.status_code == 409
    vendor.refresh_from_db()
    assert vendor.status == Vendor.Status.APPROVED


def test_public_vendor_list_only_returns_approved_stores(api_client, make_user, make_vendor):
    approved = make_vendor(
        make_user("approved@test.com"),
        store_name="Approved Store",
        slug="approved-store",
        status=Vendor.Status.APPROVED,
    )
    make_vendor(
        make_user("pending@test.com"),
        store_name="Pending Store",
        slug="pending-store",
    )
    make_vendor(
        make_user("rejected@test.com"),
        store_name="Rejected Store",
        slug="rejected-store",
        status=Vendor.Status.REJECTED,
    )

    response = api_client.get(reverse("vendors:list"))

    assert response.status_code == 200
    assert [item["id"] for item in response.data] == [approved.id]
    assert response.data[0]["slug"] == "approved-store"
    assert "owner_email" not in response.data[0]


def test_public_vendor_detail_returns_approved_store(api_client, make_user, make_vendor):
    make_vendor(
        make_user("approved@test.com"),
        store_name="Approved Store",
        slug="approved-store",
        status=Vendor.Status.APPROVED,
    )

    response = api_client.get(reverse("vendors:detail", kwargs={"slug": "approved-store"}))

    assert response.status_code == 200
    assert response.data["store_name"] == "Approved Store"
    assert response.data["slug"] == "approved-store"
    assert "owner_email" not in response.data


@pytest.mark.parametrize("vendor_status", [Vendor.Status.PENDING, Vendor.Status.REJECTED])
def test_public_vendor_detail_hides_unapproved_store(
    api_client, make_user, make_vendor, vendor_status
):
    make_vendor(
        make_user("unapproved@test.com"),
        store_name="Unapproved Store",
        slug="unapproved-store",
        status=vendor_status,
    )

    response = api_client.get(reverse("vendors:detail", kwargs={"slug": "unapproved-store"}))

    assert response.status_code == 404

from django.db import transaction

from apps.vendors.models import Vendor


class VendorStateError(Exception):
    """Raised when a vendor status transition is not allowed."""


def approve_vendor(vendor: Vendor) -> Vendor:
    with transaction.atomic():
        vendor = Vendor.objects.select_for_update().select_related("owner").get(pk=vendor.pk)
        if vendor.status != Vendor.Status.PENDING:
            raise VendorStateError("Only pending applications can be approved.")

        vendor.status = Vendor.Status.APPROVED
        vendor.save(update_fields=["status", "updated_at"])

        owner = vendor.owner
        owner.role = owner.Role.VENDOR
        owner.save(update_fields=["role"])
    return vendor


def reject_vendor(vendor: Vendor) -> Vendor:
    with transaction.atomic():
        vendor = Vendor.objects.select_for_update().get(pk=vendor.pk)
        if vendor.status != Vendor.Status.PENDING:
            raise VendorStateError("Only pending applications can be rejected.")

        vendor.status = Vendor.Status.REJECTED
        vendor.save(update_fields=["status", "updated_at"])
    return vendor

from django.contrib import admin

from apps.vendors import services
from apps.vendors.models import Vendor


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ("store_name", "owner", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("store_name", "owner__email")
    prepopulated_fields = {"slug": ("store_name",)}
    actions = ["approve_vendors", "reject_vendors"]

    @admin.action(description="Approve selected vendor applications")
    def approve_vendors(self, request, queryset):
        for vendor in queryset:
            try:
                services.approve_vendor(vendor)
            except services.VendorStateError:
                self.message_user(request, f"{vendor} skipped (not pending).", level="warning")

    @admin.action(description="Reject selected vendor applications")
    def reject_vendors(self, request, queryset):
        for vendor in queryset:
            try:
                services.reject_vendor(vendor)
            except services.VendorStateError:
                self.message_user(request, f"{vendor} skipped (not pending).", level="warning")

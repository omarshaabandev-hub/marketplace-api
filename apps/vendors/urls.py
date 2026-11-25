from django.urls import path

from apps.vendors.views import (
    AdminVendorReviewView,
    MyVendorStoreView,
    VendorApplyView,
)

app_name = "vendors"

urlpatterns = [
    path("apply/", VendorApplyView.as_view(), name="apply"),
    path("me/", MyVendorStoreView.as_view(), name="my-store"),
    path("<int:pk>/review/", AdminVendorReviewView.as_view(), name="admin-review"),
]

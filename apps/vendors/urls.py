from django.urls import path

from apps.vendors.views import (
    AdminVendorReviewView,
    MyVendorStoreView,
    PublicVendorDetailView,
    PublicVendorListView,
    VendorApplyView,
)

app_name = "vendors"

urlpatterns = [
    path("", PublicVendorListView.as_view(), name="list"),
    path("apply/", VendorApplyView.as_view(), name="apply"),
    path("me/", MyVendorStoreView.as_view(), name="my-store"),
    path("<int:pk>/review/", AdminVendorReviewView.as_view(), name="admin-review"),
    path("<slug:slug>/", PublicVendorDetailView.as_view(), name="detail"),
]

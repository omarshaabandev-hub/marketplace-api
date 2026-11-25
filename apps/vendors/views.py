from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.permissions import IsAdmin
from apps.vendors import services
from apps.vendors.models import Vendor
from apps.vendors.permissions import IsVendorOwner
from apps.vendors.serializers import (
    VendorApplySerializer,
    VendorDetailSerializer,
    VendorReviewSerializer,
)


class VendorApplyView(generics.CreateAPIView):
    """Endpoint for authenticated users to apply to become a vendor."""

    serializer_class = VendorApplySerializer
    permission_classes = (permissions.IsAuthenticated,)


class MyVendorStoreView(generics.RetrieveUpdateAPIView):
    """Endpoint for vendors to view and update their own store."""

    serializer_class = VendorDetailSerializer
    permission_classes = (permissions.IsAuthenticated, IsVendorOwner)

    def get_object(self):
        vendor = get_object_or_404(Vendor, owner=self.request.user)
        self.check_object_permissions(self.request, vendor)
        return vendor


class AdminVendorReviewView(APIView):
    """Admin endpoint to approve or reject vendor applications."""

    permission_classes = (IsAdmin,)

    def post(self, request, pk):
        serializer = VendorReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vendor = get_object_or_404(Vendor, pk=pk)
        action = serializer.validated_data["action"]

        try:
            if action == "approve":
                services.approve_vendor(vendor)
                message = f"Store '{vendor.store_name}' approved successfully."
            else:
                services.reject_vendor(vendor)
                message = f"Store '{vendor.store_name}' rejected successfully."

        except services.VendorStateError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)

        return Response({"detail": message})

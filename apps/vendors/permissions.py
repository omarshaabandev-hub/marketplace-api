from rest_framework import permissions


class IsVendorOwner(permissions.BasePermission):
    """
    Object-level permission to ensure users can only view or edit
    their own vendor store profile.
    """

    def has_object_permission(self, request, view, obj):
        return bool(request.user and request.user.is_authenticated and obj.owner == request.user)

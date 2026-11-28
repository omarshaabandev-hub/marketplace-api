from django.db import IntegrityError
from django.utils.text import slugify
from rest_framework import serializers

from apps.vendors.models import Vendor


def build_slug(name: str) -> str:
    return slugify(name, allow_unicode=True)


class VendorApplySerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = ("id", "store_name", "description", "status", "created_at")
        read_only_fields = ("id", "status", "created_at")

    def validate_store_name(self, value):
        slug = build_slug(value)
        if not slug:
            raise serializers.ValidationError("Store name must contain letters or numbers.")
        if Vendor.objects.filter(slug=slug).exists():
            raise serializers.ValidationError("A store with a similar name already exists.")
        return value

    def validate(self, attrs):
        user = self.context["request"].user
        if Vendor.objects.filter(owner=user).exists():
            raise serializers.ValidationError("You have already applied for or own a vendor store.")
        return attrs

    def create(self, validated_data):
        user = self.context["request"].user
        slug = build_slug(validated_data["store_name"])
        try:
            return Vendor.objects.create(owner=user, slug=slug, **validated_data)
        except IntegrityError as exc:
            raise serializers.ValidationError(
                "Could not create the store. The name may already be taken."
            ) from exc


class VendorDetailSerializer(serializers.ModelSerializer):
    owner_email = serializers.EmailField(source="owner.email", read_only=True)

    class Meta:
        model = Vendor
        fields = ("id", "owner_email", "store_name", "slug", "description", "status", "created_at")
        read_only_fields = ("id", "owner_email", "slug", "status", "created_at")


class PublicVendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = ("id", "store_name", "slug", "description", "created_at")
        read_only_fields = fields


class VendorReviewSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=("approve", "reject"))

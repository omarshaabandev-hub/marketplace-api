from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT Serializer to inject user claims (email & role)
    directly inside the access token payload.
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["email"] = user.email
        token["role"] = user.role
        return token


class UserRegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration. Handles password hashing
    and role validation to prevent self-assigned Admin roles.
    """

    password = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
        min_length=8,
    )

    class Meta:
        model = User
        fields = ("id", "email", "password", "first_name", "last_name", "role")
        extra_kwargs = {"role": {"required": False}}

    def validate_role(self, value):
        # Business Rule: Self-registration as ADMIN is prohibited.
        if value == User.Role.ADMIN:
            raise serializers.ValidationError("You cannot self-register as an Admin.")
        return value

    def create(self, validated_data):
        # Always use create_user to enforce password hashing (PBKDF2)
        return User.objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for viewing and updating user profile details.
    """

    class Meta:
        model = User
        fields = ("id", "email", "first_name", "last_name", "role", "date_joined")
        read_only_fields = ("id", "email", "role", "date_joined")

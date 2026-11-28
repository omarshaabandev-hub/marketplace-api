from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class MarketplaceUserChangeForm(UserChangeForm):
    username = None

    class Meta(UserChangeForm.Meta):
        model = User
        fields = "__all__"


class MarketplaceUserCreationForm(UserCreationForm):
    username = None

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("email", "role")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User._default_manager.filter(email__iexact=email).exists():
            raise ValidationError("A user with this email already exists.")
        return email


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name")}),
        (_("Role"), {"fields": ("role",)}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "role", "password1", "password2"),
            },
        ),
    )
    form = MarketplaceUserChangeForm
    add_form = MarketplaceUserCreationForm
    list_display = ("email", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_active")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("email",)
    filter_horizontal = ("groups", "user_permissions")

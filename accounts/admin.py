"""پنل مدیریت اپ accounts — سازگار با احراز هویت با شماره موبایل."""

from __future__ import annotations

from django.contrib import admin
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters

from .forms import UserAdminChangeForm, UserAdminCreationForm
from .models import PhoneOTP, Profile, User


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = "پروفایل"
    fields = (
        "national_code",
        "birth_date",
        "gender",
        "province",
        "city",
        "postal_code",
        "address",
        "avatar",
    )


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """ادمین سفارشی کاربر — USERNAME_FIELD موبایل است، پس UserAdmin پیش‌فرض جنگو کار نمی‌کند."""

    form = UserAdminChangeForm
    add_form = UserAdminCreationForm

    list_display = (
        "phone_number",
        "masked_email",
        "full_name",
        "is_active",
        "is_phone_verified",
        "is_staff",
        "date_joined",
    )

    list_filter = (
        "is_staff",
        "is_superuser",
        "is_active",
        "is_phone_verified",
    )

    search_fields = (
        "phone_number",
        "email",
        "first_name",
        "last_name",
    )

    ordering = ("-date_joined",)
    list_per_page = 30
    date_hierarchy = "date_joined"
    inlines = (ProfileInline,)

    fieldsets = (
        ("اطلاعات اصلی", {"fields": ("phone_number", "email", "first_name", "last_name")}),
        ("وضعیت", {"fields": ("is_active", "is_phone_verified", "is_staff", "is_superuser")}),
        ("گروه‌ها و دسترسی‌ها", {"fields": ("groups", "user_permissions"), "classes": ("collapse",)}),
        ("تاریخ‌ها", {"fields": ("last_login", "date_joined"), "classes": ("collapse",)}),
    )

    add_fieldsets = (
        (
            "کاربر جدید",
            {
                "classes": ("wide",),
                "fields": ("phone_number", "email", "first_name", "last_name", "password1", "password2"),
            },
        ),
    )

    readonly_fields = ("last_login", "date_joined")
    filter_horizontal = ("groups", "user_permissions")

    @method_decorator(sensitive_post_parameters())
    def add_view(self, *args, **kwargs):
        return super().add_view(*args, **kwargs)

    @admin.display(description="نام کامل")
    def full_name(self, obj: User) -> str:
        return obj.get_full_name() or "—"


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "city", "province", "completion_percent", "updated_at")
    search_fields = ("user__phone_number", "user__email", "city")
    readonly_fields = ("created_at", "updated_at")


@admin.register(PhoneOTP)
class PhoneOTPAdmin(admin.ModelAdmin):
    list_display = (
        "phone_number",
        "purpose",
        "is_used",
        "attempts",
        "is_expired_display",
        "created_at",
    )
    list_filter = ("purpose", "is_used")
    readonly_fields = (
        "phone_number",
        "purpose",
        "code_hash",
        "attempts",
        "is_used",
        "expires_at",
        "verified_at",
        "ip_address",
        "created_at",
    )

    @admin.display(description="منقضی؟", boolean=True)
    def is_expired_display(self, obj) -> bool:
        return obj.is_expired

#accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "username",
        "email",
        "phone_number",
        "first_name",
        "last_name",
        "is_staff",
        "is_active",
        "date_joined",
    )
    date_hierarchy = "date_joined"
    list_filter = ("is_staff", "is_superuser", "is_active")
    search_fields = ("username", "email", "phone_number", "first_name", "last_name")
    ordering = ("-date_joined",)
    list_per_page = 30

    fieldsets = UserAdmin.fieldsets + (
        ("اطلاعات تماس", {"fields": ("phone_number",)}),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "اطلاعات تماس",
            {"fields": ("email", "phone_number", "first_name", "last_name")},
        ),
    )

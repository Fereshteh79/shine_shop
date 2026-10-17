from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"
    verbose_name = "حساب‌های کاربری"

    def ready(self):
        # Import سیگنال‌ها — ساخت خودکار Profile
        from . import signals  # noqa: F401

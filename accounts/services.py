# accounts/services.py

from django.db import transaction

from .models import User


class AccountService:

    @staticmethod
    @transaction.atomic
    def create_user(*, form_data: dict) -> User:
        """ایجاد کاربر از داده‌های پاک‌شدهٔ فرم ثبت‌نام."""

        password = form_data.get("password1")

        if not password:
            raise ValueError("رمز عبور در داده‌های فرم وجود ندارد.")

        user = User(
            username=(form_data.get("username") or "").strip(),
            email=(form_data.get("email") or "").lower().strip(),
            phone_number=form_data.get("phone_number") or None,
            first_name=(form_data.get("first_name") or "").strip(),
            last_name=(form_data.get("last_name") or "").strip(),
        )

        user.set_password(password)
        user.full_clean(exclude=["password"])
        user.save()

        return user

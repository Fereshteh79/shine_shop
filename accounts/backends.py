"""بک‌اند احراز هویت با شماره موبایل یا ایمیل."""

from __future__ import annotations

from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

from accounts.selectors import find_user_by_identifier

UserModel = get_user_model()


class PhoneOrEmailBackend(ModelBackend):
    """
    احراز هویت با شماره موبایل یا ایمیل + رمز عبور.

    شناسه ورودی می‌تواند:
        - شماره موبایل
        - ایمیل
    باشد.
    """

    def authenticate(
            self,
            request: Any,
            username: str | None = None,
            password: str | None = None,
            **kwargs: Any,
    ):
        identifier = (
                username
                or kwargs.get(UserModel.USERNAME_FIELD)
                or kwargs.get("email")
        )

        if not identifier or password is None:
            return None

        user = find_user_by_identifier(identifier)

        if user is None:
            # برای نزدیک کردن زمان پاسخ به حالت وجود داشتن کاربر،
            # یک password hash واقعی محاسبه می‌کنیم.
            UserModel().set_password(password)
            return None

        if not user.check_password(password):
            return None

        if not self.user_can_authenticate(user):
            return None

        return user

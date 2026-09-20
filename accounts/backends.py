from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

User = get_user_model()


class EmailOrPhoneModelBackend(ModelBackend):
    """احراز هویت با نام کاربری، ایمیل یا شماره موبایل + رمز عبور."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)

        if username is None or password is None:
            return None

        try:
            user = User.objects.get(
                Q(username__iexact=username)
                | Q(email__iexact=username)
                | Q(phone_number=username)
            )
        except User.DoesNotExist:
            # اجرای هش رمز برای جلوگیری از حمله زمانی (timing attack)
            User().set_password(password)
            return None
        except User.MultipleObjectsReturned:
            return None

        if self.user_can_authenticate(user) and user.check_password(password):
            return user

        return None

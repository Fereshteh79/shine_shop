"""فرم‌های اپ accounts."""

from __future__ import annotations

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import Profile, User
from .utils import normalize_email, normalize_phone
from .validators import validate_iranian_mobile

INPUT_CLASS = "form-input"
MAX_IDENTIFIER_LENGTH = 254
OTP_CODE_LENGTH = 6


class IranianMobileField(forms.CharField):
    """
    فیلد شماره موبایل ایران.

    ورودی قبل از validation نرمال می‌شود تا فرمت‌های مختلف
    شماره موبایل به یک مقدار استاندارد تبدیل شوند.
    """

    def __init__(self, **kwargs):
        kwargs.setdefault("max_length", 11)
        kwargs.setdefault("validators", [validate_iranian_mobile])
        super().__init__(**kwargs)

    def to_python(self, value):
        value = super().to_python(value)
        return normalize_phone(value or "")


class RegisterForm(forms.ModelForm):
    """فرم ثبت‌نام کاربر."""

    phone_number = IranianMobileField(
        label="شماره موبایل",
        widget=forms.TextInput(
            attrs={
                "class": INPUT_CLASS,
                "inputmode": "numeric",
                "autocomplete": "tel",
                "placeholder": "09121234567",
            }
        ),
    )

    password1 = forms.CharField(
        label="رمز عبور",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": INPUT_CLASS,
                "autocomplete": "new-password",
                "placeholder": "••••••••",
            }
        ),
    )

    password2 = forms.CharField(
        label="تکرار رمز عبور",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": INPUT_CLASS,
                "autocomplete": "new-password",
                "placeholder": "تکرار رمز عبور",
            }
        ),
    )

    class Meta:
        model = User
        fields = (
            "phone_number",
            "first_name",
            "last_name",
            "email",
        )
        widgets = {
            "first_name": forms.TextInput(
                attrs={
                    "class": INPUT_CLASS,
                    "autocomplete": "given-name",
                    "placeholder": "نام",
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "class": INPUT_CLASS,
                    "autocomplete": "family-name",
                    "placeholder": "نام خانوادگی",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": INPUT_CLASS,
                    "autocomplete": "email",
                    "dir": "ltr",
                    "placeholder": "you@example.com",
                }
            ),
        }

    def clean_email(self):
        email = normalize_email(self.cleaned_data.get("email") or "")

        if email and User.objects.filter(email__iexact=email).exists():
            raise ValidationError("این ایمیل قبلاً ثبت شده است.", code="duplicate_email")

        return email

    def clean_phone_number(self):
        phone = self.cleaned_data.get("phone_number") or ""

        if User.objects.filter(phone_number=phone).exists():
            raise ValidationError("این شماره موبایل قبلاً ثبت شده است.", code="duplicate_phone")

        return phone

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        if not password1 or not password2:
            return password2

        if password1 != password2:
            raise ValidationError(
                "دو رمز عبور یکسان نیستند.",
                code="password_mismatch",
            )

        user = User(
            phone_number=self.cleaned_data.get("phone_number", ""),
            first_name=self.cleaned_data.get("first_name", ""),
            last_name=self.cleaned_data.get("last_name", ""),
            email=self.cleaned_data.get("email"),
        )

        validate_password(password1, user=user)

        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])

        if commit:
            user.save()

        return user


class LoginForm(AuthenticationForm):
    """ورود با شماره موبایل یا ایمیل."""

    username = forms.CharField(
        label="شماره موبایل یا ایمیل",
        max_length=MAX_IDENTIFIER_LENGTH,
        widget=forms.TextInput(
            attrs={
                "class": INPUT_CLASS,
                "autofocus": True,
                "autocomplete": "username",
                "placeholder": "09121234567 یا you@example.com",
                "maxlength": str(MAX_IDENTIFIER_LENGTH),
            }
        ),
    )

    password = forms.CharField(
        label="رمز عبور",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": INPUT_CLASS,
                "autocomplete": "current-password",
                "placeholder": "••••••••",
            }
        ),
    )

    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": "شماره موبایل/ایمیل یا رمز عبور اشتباه است.",
    }


class OtpRequestForm(forms.Form):
    """درخواست ارسال کد OTP."""

    phone_number = IranianMobileField(
        label="شماره موبایل",
        widget=forms.TextInput(
            attrs={
                "class": INPUT_CLASS,
                "inputmode": "numeric",
                "autocomplete": "tel",
                "placeholder": "09121234567",
            }
        ),
    )


class OtpVerifyForm(forms.Form):
    """تأیید کد OTP."""

    code = forms.CharField(
        label="کد تأیید",
        min_length=OTP_CODE_LENGTH,
        max_length=OTP_CODE_LENGTH,
        strip=True,
        widget=forms.TextInput(
            attrs={
                "class": INPUT_CLASS,
                "inputmode": "numeric",
                "autocomplete": "one-time-code",
                "placeholder": "- - - - - -",
                "dir": "ltr",
                "maxlength": str(OTP_CODE_LENGTH),
            }
        ),
    )

    def clean_code(self):
        from .utils import normalize_digits

        return normalize_digits(self.cleaned_data.get("code") or "").strip()


class ProfileForm(forms.ModelForm):
    """فرم اطلاعات پروفایل."""

    class Meta:
        model = Profile
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
        widgets = {
            "national_code": forms.TextInput(
                attrs={
                    "class": INPUT_CLASS,
                    "inputmode": "numeric",
                    "dir": "ltr",
                }
            ),
            "birth_date": forms.DateInput(
                format="%Y-%m-%d",
                attrs={
                    "class": INPUT_CLASS,
                    "type": "date",
                },
            ),
            "gender": forms.Select(attrs={"class": INPUT_CLASS}),
            "province": forms.TextInput(attrs={"class": INPUT_CLASS}),
            "city": forms.TextInput(attrs={"class": INPUT_CLASS}),
            "postal_code": forms.TextInput(
                attrs={
                    "class": INPUT_CLASS,
                    "inputmode": "numeric",
                    "dir": "ltr",
                }
            ),
            "address": forms.Textarea(
                attrs={
                    "class": INPUT_CLASS,
                    "rows": 3,
                }
            ),
            "avatar": forms.ClearableFileInput(
                attrs={
                    "class": INPUT_CLASS,
                    "accept": "image/*",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["birth_date"].input_formats = ["%Y-%m-%d"]

    def clean_national_code(self):
        from .utils import normalize_national_code
        from .validators import validate_iranian_national_code

        code = normalize_national_code(self.cleaned_data.get("national_code") or "")
        validate_iranian_national_code(code)
        return code

    def clean_postal_code(self):
        from core.validators import is_valid_postal_code, normalize_postal_code

        code = normalize_postal_code(self.cleaned_data.get("postal_code") or "")

        if code and not is_valid_postal_code(code):
            raise ValidationError("کد پستی واردشده معتبر نیست.", code="invalid_postal_code")

        return code


class UserAdminCreationForm(forms.ModelForm):
    """فرم ساخت User در پنل مدیریت."""

    password1 = forms.CharField(
        label="رمز عبور",
        strip=False,
        widget=forms.PasswordInput,
    )

    password2 = forms.CharField(
        label="تکرار رمز عبور",
        strip=False,
        widget=forms.PasswordInput,
    )

    class Meta:
        model = User
        fields = (
            "phone_number",
            "email",
            "first_name",
            "last_name",
        )

    def clean_email(self):
        return normalize_email(self.cleaned_data.get("email") or "")

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        if not password1 or not password2:
            return password2

        if password1 != password2:
            raise ValidationError(
                "دو رمز عبور یکسان نیستند.",
                code="password_mismatch",
            )

        validate_password(password2)

        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])

        if commit:
            user.save()

        return user


class UserAdminChangeForm(forms.ModelForm):
    """فرم ویرایش User در پنل مدیریت."""

    password = forms.CharField(
        label="رمز عبور",
        help_text="رمز عبور به‌صورت هش ذخیره می‌شود و قابل مشاهده نیست.",
        widget=forms.PasswordInput(render_value=False),
        required=False,
    )

    class Meta:
        model = User
        fields = "__all__"

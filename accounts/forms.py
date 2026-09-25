# accounts/forms.py

import re

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User

WIDGET_ATTRS = {"class": "form-input"}
PERSIAN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")


class RegisterForm(UserCreationForm):
    """فرم ثبت‌نام با اعتبارسنجی ایمیل و شماره موبایل."""

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "phone_number",
            "first_name",
            "last_name",
            "password1",
            "password2",
        )
        widgets = {
            "username": forms.TextInput(
                attrs={
                    **WIDGET_ATTRS,
                    "autocomplete": "username",
                    "placeholder": "مثلاً shahab_t",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    **WIDGET_ATTRS,
                    "autocomplete": "email",
                    "placeholder": "you@example.com",
                    "dir": "ltr",
                }
            ),
            "phone_number": forms.TextInput(
                attrs={
                    **WIDGET_ATTRS,
                    "autocomplete": "tel",
                    "placeholder": "09123456789",
                    "dir": "ltr",
                    "inputmode": "numeric",
                }
            ),
            "first_name": forms.TextInput(
                attrs={**WIDGET_ATTRS, "placeholder": "نام"}
            ),
            "last_name": forms.TextInput(
                attrs={**WIDGET_ATTRS, "placeholder": "نام خانوادگی"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["password1"].widget.attrs.update(
            {
                **WIDGET_ATTRS,
                "autocomplete": "new-password",
                "placeholder": "••••••••",
            }
        )
        self.fields["password2"].widget.attrs.update(
            {
                **WIDGET_ATTRS,
                "autocomplete": "new-password",
                "placeholder": "تکرار رمز عبور",
            }
        )
        self.fields["password1"].help_text = "حداقل ۸ کاراکتر؛ شامل حرف و عدد."
        self.fields["password2"].help_text = None

    def clean_email(self):
        email = self.cleaned_data.get("email", "").lower().strip()

        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("این ایمیل قبلاً ثبت شده است.")

        return email

    def clean_phone_number(self):
        phone = (self.cleaned_data.get("phone_number") or "").strip()
        phone = phone.translate(PERSIAN_DIGITS)

        if not re.fullmatch(r"09\d{9}", phone):
            raise forms.ValidationError(
                "شماره موبایل باید با ۰۹ شروع شده و ۱۱ رقم باشد."
            )

        if User.objects.filter(phone_number=phone).exists():
            raise forms.ValidationError(
                "این شماره موبایل قبلاً ثبت شده است."
            )

        return phone

    def clean_username(self):
        return (self.cleaned_data.get("username") or "").strip()


class LoginForm(AuthenticationForm):
    """فرم ورود با نام کاربری، ایمیل یا شماره موبایل."""

    username = forms.CharField(
        label="نام کاربری، ایمیل یا موبایل",
        widget=forms.TextInput(
            attrs={
                "class": "form-input",
                "autocomplete": "username",
                "placeholder": "نام کاربری، ایمیل یا موبایل",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["password"].widget.attrs.update(
            {
                "class": "form-input",
                "autocomplete": "current-password",
                "placeholder": "••••••••",
            }
        )


class OtpRequestForm(forms.Form):
    """فرم درخواست کد یکبارمصرف."""

    phone_number = forms.CharField(
        label="شماره موبایل",
        max_length=11,
        widget=forms.TextInput(
            attrs={
                "class": "form-input",
                "placeholder": "09123456789",
                "dir": "ltr",
                "inputmode": "numeric",
                "autocomplete": "tel",
            }
        ),
    )

    def clean_phone_number(self):
        phone = (self.cleaned_data.get("phone_number") or "").strip()
        phone = phone.translate(PERSIAN_DIGITS)

        if not re.fullmatch(r"09\d{9}", phone):
            raise forms.ValidationError(
                "شماره موبایل باید با ۰۹ شروع شده و ۱۱ رقم باشد."
            )

        return phone


class OtpVerifyForm(forms.Form):
    """فرم بررسی کد یکبارمصرف."""

    code = forms.CharField(
        label="کد پیامک‌شده",
        max_length=6,
        min_length=6,
        widget=forms.TextInput(
            attrs={
                "class": "form-input otp-code-input",
                "placeholder": "------",
                "dir": "ltr",
                "inputmode": "numeric",
                "autocomplete": "one-time-code",
            }
        ),
    )

    def clean_code(self):
        code = (self.cleaned_data.get("code") or "").strip()
        code = code.translate(PERSIAN_DIGITS)

        if not re.fullmatch(r"\d{6}", code):
            raise forms.ValidationError("کد باید ۶ رقم باشد.")

        return code

import re

from django import forms


class CheckoutForm(forms.Form):
    recipient_name = forms.CharField(
        max_length=150,
        label="نام گیرنده",
        widget=forms.TextInput(
            attrs={
                "autocomplete": "name",
                "placeholder": "نام و نام خانوادگی",
            }
        ),
    )

    phone_number = forms.CharField(
        max_length=20,
        label="شماره تماس",
        widget=forms.TextInput(
            attrs={
                "autocomplete": "tel",
                "inputmode": "tel",
                "placeholder": "09xxxxxxxxx",
            }
        ),
    )

    province = forms.CharField(
        max_length=100,
        label="استان",
        widget=forms.TextInput(
            attrs={
                "placeholder": "استان",
            }
        ),
    )

    city = forms.CharField(
        max_length=100,
        label="شهر",
        widget=forms.TextInput(
            attrs={
                "placeholder": "شهر",
            }
        ),
    )

    address = forms.CharField(
        label="آدرس",
        widget=forms.Textarea(
            attrs={
                "rows": 4,
                "placeholder": "آدرس کامل محل تحویل",
            }
        ),
    )

    postal_code = forms.CharField(
        max_length=20,
        label="کد پستی",
        widget=forms.TextInput(
            attrs={
                "inputmode": "numeric",
                "placeholder": "کد پستی ۱۰ رقمی",
            }
        ),
    )

    notes = forms.CharField(
        required=False,
        label="توضیحات",
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "placeholder": "توضیحات تکمیلی برای سفارش...",
            }
        ),
    )

    def clean_recipient_name(self):
        value = self.cleaned_data["recipient_name"].strip()

        if len(value) < 3:
            raise forms.ValidationError(
                "نام گیرنده معتبر نیست."
            )

        return value

    def clean_phone_number(self):
        value = self.cleaned_data["phone_number"].strip()
        value = value.replace(" ", "").replace("-", "")

        if value.startswith("+98"):
            value = "0" + value[3:]

        if not re.fullmatch(r"09\d{9}", value):
            raise forms.ValidationError(
                "شماره موبایل معتبر نیست."
            )

        return value

    def clean_postal_code(self):
        value = self.cleaned_data["postal_code"].strip()
        value = value.replace(" ", "").replace("-", "")

        if not re.fullmatch(r"\d{10}", value):
            raise forms.ValidationError(
                "کد پستی باید ۱۰ رقم باشد."
            )

        return value
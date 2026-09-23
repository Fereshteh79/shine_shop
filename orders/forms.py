import re

from django import forms


class CheckoutForm(forms.Form):
    recipient_name = forms.CharField(
        max_length=150,
        label="نام گیرنده",
        strip=True,
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
        strip=True,
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
        strip=True,
        widget=forms.TextInput(
            attrs={
                "autocomplete": "address-level1",
                "placeholder": "استان",
            }
        ),
    )

    city = forms.CharField(
        max_length=100,
        label="شهر",
        strip=True,
        widget=forms.TextInput(
            attrs={
                "autocomplete": "address-level2",
                "placeholder": "شهر",
            }
        ),
    )

    address = forms.CharField(
        label="آدرس",
        strip=True,
        widget=forms.Textarea(
            attrs={
                "autocomplete": "street-address",
                "rows": 4,
                "placeholder": "آدرس کامل محل تحویل",
            }
        ),
    )

    postal_code = forms.CharField(
        max_length=10,
        label="کد پستی",
        strip=True,
        widget=forms.TextInput(
            attrs={
                "autocomplete": "postal-code",
                "inputmode": "numeric",
                "placeholder": "کد پستی ۱۰ رقمی",
            }
        ),
    )

    notes = forms.CharField(
        required=False,
        label="توضیحات",
        strip=True,
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "placeholder": "توضیحات تکمیلی برای سفارش...",
            }
        ),
    )

    def clean_recipient_name(self):
        value = self.cleaned_data["recipient_name"]

        if len(value) < 3:
            raise forms.ValidationError(
                "نام گیرنده معتبر نیست."
            )

        return value

    def clean_phone_number(self):
        value = self.cleaned_data["phone_number"]

        value = re.sub(r"[\s-]+", "", value)

        if value.startswith("+98"):
            value = "0" + value[3:]

        if not re.fullmatch(r"09\d{9}", value, re.ASCII):
            raise forms.ValidationError(
                "شماره موبایل معتبر نیست."
            )

        return value

    def clean_postal_code(self):
        value = self.cleaned_data["postal_code"]

        value = re.sub(r"[\s-]+", "", value)

        if not re.fullmatch(r"\d{10}", value, re.ASCII):
            raise forms.ValidationError(
                "کد پستی باید ۱۰ رقم باشد."
            )

        return value

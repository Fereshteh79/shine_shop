from django import forms

PERSIAN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")


def to_english_digits(value: str) -> str:
    """تبدیل ارقام فارسی/عربی به لاتین."""
    return value.translate(PERSIAN_DIGITS).translate(ARABIC_DIGITS)


class AddToCartForm(forms.Form):
    """فرم افزودن محصول به سبد — مرجع واحد؛ products/forms.py آن را re-export می‌کند."""

    quantity = forms.IntegerField(
        min_value=1,
        max_value=99,
        initial=1,
        label="تعداد",
    )

    variant = forms.IntegerField(
        required=False,
        min_value=1,
        label="تنوع",
        widget=forms.HiddenInput(),
    )

    def clean_quantity(self):
        raw = to_english_digits(str(self.data.get("quantity", "")))

        try:
            quantity = int(raw)
        except (TypeError, ValueError):
            raise forms.ValidationError("تعداد باید یک عدد معتبر باشد.")

        if quantity < 1:
            raise forms.ValidationError("تعداد باید بیشتر از صفر باشد.")

        if quantity > 99:
            raise forms.ValidationError("حداکثر تعداد هر کالا ۹۹ عدد است.")

        return quantity


class UpdateCartItemForm(forms.Form):
    quantity = forms.IntegerField(
        min_value=1,
        max_value=99,
        label="تعداد",
    )

    def clean_quantity(self):
        raw = to_english_digits(str(self.data.get("quantity", "")))

        try:
            quantity = int(raw)
        except (TypeError, ValueError):
            raise forms.ValidationError("تعداد باید یک عدد معتبر باشد.")

        if quantity < 1 or quantity > 99:
            raise forms.ValidationError("تعداد باید بین ۱ تا ۹۹ باشد.")

        return quantity

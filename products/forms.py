from django import forms

from .models import Product

# re-export: ویوهای products از همین مسیر import می‌کنند
from cart.forms import AddToCartForm  # noqa: F401


class ProductSearchForm(forms.Form):
    q = forms.CharField(
        required=False,
        max_length=100,
        label="جستجو",
        widget=forms.TextInput(
            attrs={
                "placeholder": "نام محصول...",
                "autocomplete": "off",
            },
        ),
    )


class ProductAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()

        price = cleaned_data.get("price")
        discount_price = cleaned_data.get("discount_price")

        if (
                price is not None
                and discount_price is not None
                and discount_price >= price
        ):
            self.add_error(
                "discount_price",
                "قیمت تخفیف باید کمتر از قیمت اصلی باشد.",
            )

        return cleaned_data

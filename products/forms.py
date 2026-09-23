from django import forms

from .models import Product


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


class AddToCartForm(forms.Form):
    quantity = forms.IntegerField(
        min_value=1,
        max_value=99,
        initial=1,
        label="تعداد",
        widget=forms.NumberInput(
            attrs={
                "min": 1,
                "max": 99,
                "inputmode": "numeric",
            },
        ),
    )

    variant = forms.IntegerField(
        required=False,
        min_value=1,
        label="تنوع",
        widget=forms.HiddenInput(),
    )

    def clean_quantity(self):
        quantity = self.cleaned_data["quantity"]

        if quantity < 1:
            raise forms.ValidationError(
                "تعداد باید بیشتر از صفر باشد."
            )

        return quantity

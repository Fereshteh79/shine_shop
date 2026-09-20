from django import forms


class AddToCartForm(forms.Form):
    """فرم افزودن محصول به سبد خرید — نام فیلدها با قالب جزئیات محصول هماهنگ است."""

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
        quantity = self.cleaned_data["quantity"]

        if quantity <= 0:
            raise forms.ValidationError("تعداد باید بیشتر از صفر باشد.")

        return quantity


class UpdateCartItemForm(forms.Form):
    quantity = forms.IntegerField(
        min_value=1,
        max_value=99,
        label="تعداد",
    )

from django import forms


class WishlistProductForm(forms.Form):
    product_id = forms.IntegerField(
        min_value=1,
        widget=forms.HiddenInput(),
    )

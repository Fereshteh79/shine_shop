from django import forms


class PaymentStartForm(forms.Form):
    gateway = forms.ChoiceField(
        choices=(
            ("zarinpal", "زرین‌پال"),
        ),
        widget=forms.HiddenInput(),
        initial="zarinpal",
    )

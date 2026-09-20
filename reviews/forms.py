from django import forms

from .models import Review


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = (
            "rating",
            "title",
            "comment",
        )

        widgets = {
            "rating": forms.RadioSelect(
                choices=(
                    (5, "۵"),
                    (4, "۴"),
                    (3, "۳"),
                    (2, "۲"),
                    (1, "۱"),
                ),
            ),
            "title": forms.TextInput(
                attrs={
                    "class": "form-input",
                    "placeholder": "عنوان دیدگاه",
                    "maxlength": 150,
                },
            ),
            "comment": forms.Textarea(
                attrs={
                    "class": "form-input",
                    "rows": 5,
                    "placeholder": "نظر خود درباره این محصول را بنویسید...",
                },
            ),
        }

    def clean_comment(self):
        comment = self.cleaned_data["comment"].strip()

        if len(comment) < 10:
            raise forms.ValidationError(
                "متن دیدگاه باید حداقل ۱۰ کاراکتر باشد."
            )

        return comment

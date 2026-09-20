from decimal import Decimal

from django.core.exceptions import ValidationError


def validate_positive_decimal(value: Decimal) -> None:
    if value <= Decimal("0"):
        raise ValidationError("مقدار باید بزرگ‌تر از صفر باشد.")


def validate_non_negative_decimal(value: Decimal) -> None:
    if value < Decimal("0"):
        raise ValidationError("مقدار نمی‌تواند منفی باشد.")


def validate_file_size(file, max_size_mb: int = 5) -> None:
    if not file:
        return

    max_size = max_size_mb * 1024 * 1024

    if file.size > max_size:
        raise ValidationError(
            f"حجم فایل نباید بیشتر از {max_size_mb} مگابایت باشد."
        )


def validate_image_file(file) -> None:
    validate_file_size(file)

    content_type = getattr(file, "content_type", "")

    if content_type and not content_type.startswith("image/"):
        raise ValidationError("فایل انتخاب‌شده باید تصویر باشد.")

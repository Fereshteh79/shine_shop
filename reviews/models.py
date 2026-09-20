from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Review(models.Model):
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="محصول",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="کاربر",
    )

    rating = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5),
        ],
        verbose_name="امتیاز",
    )

    title = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="عنوان",
    )

    comment = models.TextField(
        verbose_name="متن دیدگاه",
    )

    is_approved = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name="تأیید شده",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ایجاد",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخرین بروزرسانی",
    )

    class Meta:
        verbose_name = "دیدگاه"
        verbose_name_plural = "دیدگاه‌ها"
        ordering = ("-created_at",)

        constraints = [
            models.UniqueConstraint(
                fields=("product", "user"),
                name="unique_review_per_product_user",
            ),
        ]

        indexes = [
            models.Index(
                fields=("product", "is_approved", "-created_at"),
            ),
            models.Index(
                fields=("user", "-created_at"),
            ),
        ]

    def __str__(self):
        return f"{self.user} - {self.product} - {self.rating}"

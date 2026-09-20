from django.conf import settings
from django.db import models


class Wishlist(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wishlist",
        verbose_name="کاربر",
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
        verbose_name = "لیست علاقه‌مندی"
        verbose_name_plural = "لیست‌های علاقه‌مندی"

    def __str__(self):
        return f"علاقه‌مندی {self.user}"


class WishlistItem(models.Model):
    wishlist = models.ForeignKey(
        Wishlist,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="لیست علاقه‌مندی",
    )
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="wishlist_items",
        verbose_name="محصول",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ افزودن",
    )

    class Meta:
        verbose_name = "محصول علاقه‌مندی"
        verbose_name_plural = "محصولات علاقه‌مندی"
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("wishlist", "product"),
                name="unique_wishlist_product",
            ),
        ]

    def __str__(self):
        return self.product.name

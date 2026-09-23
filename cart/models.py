from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Q


class TimeStampedCartModel(models.Model):
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ایجاد",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخرین بروزرسانی",
    )

    class Meta:
        abstract = True


class Cart(TimeStampedCartModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cart",
        verbose_name="کاربر",
    )

    class Meta:
        verbose_name = "سبد خرید"
        verbose_name_plural = "سبدهای خرید"

    def __str__(self):
        return f"سبد خرید {self.user}"

    @property
    def total_items(self) -> int:
        """تعداد کل کالاها."""
        return sum(
            item.quantity
            for item in self.items.all()
        )

    @property
    def subtotal(self) -> Decimal:
        """جمع کل مبلغ سبد خرید."""
        total = Decimal("0.00")

        for item in self.items.all():
            total += item.line_total

        return total

    @property
    def is_empty(self) -> bool:
        return not self.items.exists()


class CartItem(TimeStampedCartModel):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="سبد خرید",
    )

    product = models.ForeignKey(
        "products.Product",
        on_delete=models.PROTECT,
        related_name="cart_items",
        verbose_name="محصول",
    )

    variant = models.ForeignKey(
        "products.ProductVariant",
        on_delete=models.PROTECT,
        related_name="cart_items",
        null=True,
        blank=True,
        verbose_name="تنوع",
    )

    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name="تعداد",
    )

    class Meta:
        verbose_name = "آیتم سبد خرید"
        verbose_name_plural = "آیتم‌های سبد خرید"
        ordering = ("created_at",)

        constraints = [
            models.UniqueConstraint(
                fields=("cart", "product", "variant"),
                condition=Q(variant__isnull=False),
                name="unique_cart_product_with_variant",
            ),
            models.UniqueConstraint(
                fields=("cart", "product"),
                condition=Q(variant__isnull=True),
                name="unique_cart_product_without_variant",
            ),
        ]

        indexes = [
            models.Index(
                fields=("cart", "product"),
            ),
        ]

    def __str__(self):
        return f"{self.product.name} × {self.quantity}"

    @property
    def unit_price(self) -> Decimal:
        if self.variant_id:
            return self.variant.final_price

        return self.product.final_price

    @property
    def line_total(self) -> Decimal:
        return self.unit_price * self.quantity

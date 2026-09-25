from django.conf import settings
from django.db import models
from django.db.models import Q

from core.constants import PaymentStatus


class Payment(models.Model):
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.PROTECT,
        related_name="payments",
        verbose_name="سفارش",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="payments",
        verbose_name="کاربر",
    )

    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name="مبلغ",
    )

    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        db_index=True,
        verbose_name="وضعیت",
    )

    gateway = models.CharField(
        max_length=50,
        verbose_name="درگاه",
    )

    authority = models.CharField(
        max_length=255,
        blank=True,
        db_index=True,
        verbose_name="شناسه درگاه",
    )

    reference_id = models.CharField(
        max_length=255,
        blank=True,
        db_index=True,
        verbose_name="کد پیگیری",
    )

    transaction_id = models.CharField(
        max_length=255,
        unique=True,
        verbose_name="شناسه تراکنش داخلی",
    )

    callback_url = models.URLField(
        blank=True,
        verbose_name="آدرس بازگشت",
    )

    payment_url = models.URLField(
        blank=True,
        verbose_name="آدرس پرداخت",
    )

    gateway_response = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="پاسخ درگاه",
    )

    error_message = models.TextField(
        blank=True,
        verbose_name="خطا",
    )

    paid_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="تاریخ پرداخت",
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
        verbose_name = "پرداخت"
        verbose_name_plural = "پرداخت‌ها"
        ordering = ("-created_at",)

        indexes = [
            models.Index(
                fields=("order", "-created_at"),
            ),
            models.Index(
                fields=("user", "-created_at"),
            ),
            models.Index(
                fields=("status", "-created_at"),
            ),
        ]

        constraints = [
            models.UniqueConstraint(
                fields=("authority",),
                condition=~Q(authority=""),
                name="unique_payment_authority",
            ),
            models.UniqueConstraint(
                fields=("order",),
                condition=Q(
                    status=PaymentStatus.SUCCESS
                ),
                name="unique_successful_payment_per_order",
            ),
        ]

    def __str__(self):
        return self.transaction_id

    @property
    def is_successful(self):
        return self.status == PaymentStatus.SUCCESS

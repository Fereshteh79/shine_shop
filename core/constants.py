"""
ثابت‌های مشترک پروژه Shine Shop.

این فایل شامل:
- وضعیت‌های سفارش
- وضعیت‌های پرداخت
- کد درگاه‌های پرداخت
- واحدهای پول
- گروه‌بندی وضعیت‌های سفارش

است.

برای مقادیر قابل ذخیره در دیتابیس از Django TextChoices استفاده شده
تا هم مقدار داخلی و هم عنوان نمایشی مشخص باشد.
"""

from __future__ import annotations

from django.db import models


# ============================================================================
# Order Status
# ============================================================================


class OrderStatus(models.TextChoices):
    """وضعیت‌های چرخه عمر سفارش."""

    PENDING = "pending", "در انتظار پرداخت"
    PAID = "paid", "پرداخت شده"
    PROCESSING = "processing", "در حال پردازش"
    SHIPPED = "shipped", "ارسال شده"
    DELIVERED = "delivered", "تحویل داده شده"
    CANCELLED = "cancelled", "لغو شده"


# ============================================================================
# Payment Status
# ============================================================================


class PaymentStatus(models.TextChoices):
    """وضعیت‌های تراکنش پرداخت."""

    PENDING = "pending", "در انتظار"
    SUCCESS = "success", "موفق"
    FAILED = "failed", "ناموفق"
    CANCELLED = "cancelled", "لغو شده"


# ============================================================================
# Payment Gateway
# ============================================================================


class GatewayCode(models.TextChoices):
    """کد درگاه‌های پرداخت پشتیبانی‌شده."""

    ZARINPAL = "zarinpal", "زرین‌پال"


# ============================================================================
# Currency
# ============================================================================


class Currency(models.TextChoices):
    """واحدهای پول پشتیبانی‌شده."""

    TOMAN = "toman", "تومان"
    RIAL = "rial", "ریال"


# ============================================================================
# Order Status Groups
# ============================================================================

# سفارش‌هایی که چرخه عمرشان به پایان رسیده و دیگر نباید
# از طریق عملیات عادی تغییر وضعیت داده شوند.
ORDER_TERMINAL_STATUSES = frozenset(
    {
        OrderStatus.DELIVERED,
        OrderStatus.CANCELLED,
    }
)

# سفارش‌هایی که هنوز در چرخه پردازش هستند.
ORDER_ACTIVE_STATUSES = frozenset(
    {
        OrderStatus.PENDING,
        OrderStatus.PAID,
        OrderStatus.PROCESSING,
        OrderStatus.SHIPPED,
    }
)

# ============================================================================
# Backward Compatibility
# ============================================================================

# نام‌های سازگار با نسخه‌های قبلی پروژه.
#
# این مقادیر را می‌توان در Modelها، Formها، Filterها و بخش‌های قدیمی
# پروژه بدون نیاز به تغییر فوری استفاده کرد.

ORDER_STATUS_CHOICES = OrderStatus.choices

PAYMENT_STATUS_CHOICES = PaymentStatus.choices

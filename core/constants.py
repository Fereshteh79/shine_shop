"""منبع واحد حقیقت برای وضعیتها، درگاهها و مقادیر ثابت پروژه."""
from __future__ import annotations

from decimal import Decimal

from django.db import models

# ---------------------------------------------------------------- پول
DECIMAL_PLACES = 2
ZERO = Decimal("0.00")
DEFAULT_CURRENCY = "IRR"


# ---------------------------------------------------------------- وضعیت سفارش
class OrderStatus(models.TextChoices):
    PENDING = "pending", "در انتظار پرداخت"
    PAID = "paid", "پرداختشده"
    PROCESSING = "processing", "در حال پردازش"
    SHIPPED = "shipped", "ارسالشده"
    DELIVERED = "delivered", "تحویلشده"
    CANCELLED = "cancelled", "لغوشده"
    REFUNDED = "refunded", "بازگشتوجهشده"

    @classmethod
    def purchased(cls) -> frozenset[str]:
        """وضعیتهایی که «خرید موفق» محسوب میشوند (برای ثبت دیدگاه و ...)."""
        return frozenset({cls.PAID, cls.PROCESSING, cls.SHIPPED, cls.DELIVERED})

    @classmethod
    def final(cls) -> frozenset[str]:
        """وضعیتهای پایانی: دیگر تغییر نمیکنند."""
        return frozenset({cls.DELIVERED, cls.CANCELLED, cls.REFUNDED})

    @classmethod
    def cancellable(cls) -> frozenset[str]:
        """فقط سفارشهایی که کاربر مجاز است لغو کند."""
        return frozenset({cls.PENDING, cls.PAID, cls.PROCESSING})

    @classmethod
    def holding_stock(cls) -> frozenset[str]:
        """وضعیتهایی که موجودی برای آنها رزرو/کسر شده است."""
        return frozenset({cls.PENDING, cls.PAID, cls.PROCESSING, cls.SHIPPED, cls.DELIVERED})


# ---------------------------------------------------------------- وضعیت پرداخت
class PaymentStatus(models.TextChoices):
    INITIATED = "initiated", "آغازشده"
    PENDING = "pending", "در انتظار نتیجه"
    SUCCESS = "success", "موفق"
    FAILED = "failed", "ناموفق"
    CANCELLED = "cancelled", "لغوشده"
    REFUNDED = "refunded", "بازگشتوجهشده"

    @classmethod
    def final(cls) -> frozenset[str]:
        return frozenset({cls.SUCCESS, cls.FAILED, cls.CANCELLED, cls.REFUNDED})

    @classmethod
    def open_statuses(cls) -> frozenset[str]:
        """پرداختهای باز: نه موفق، نه بسته. برای بستن هنگام لغو سفارش."""
        return frozenset({cls.INITIATED, cls.PENDING})


# ---------------------------------------------------------------- درگاه پرداخت
class GatewayName(models.TextChoices):
    ZARINPAL = "zarinpal", "زرینپال"
    # درگاههای بعدی اینجا اضافه میشوند؛ هیچجای دیگری هاردکد نکن.


# ---------------------------------------------------------------- هدف OTP
class OTPPurpose(models.TextChoices):
    REGISTER = "register", "ثبتنام"
    LOGIN = "login", "ورود"
    RESET_PASSWORD = "reset_password", "بازیابی رمز عبور"
    CHANGE_PHONE = "change_phone", "تغییر شماره تلفن"


# نام سازگار با کدهای فعلی (تا وقتی همهجا مهاجرت شود)
Purpose = OTPPurpose

# ---------------------------------------------------------------- محدودیتها
MAX_CART_ITEMS = 50  # حداکثر تعداد ردیف متمایز در سبد خرید
MAX_CART_ITEM_QUANTITY = 99  # حداکثر تعداد هر ردیف
MAX_PRODUCT_IMAGES = 8
REVIEW_MIN_RATING = 1
REVIEW_MAX_RATING = 5

DEFAULT_ORDER_PAYMENT_TIMEOUT_MINUTES = 30
DEFAULT_OTP_LENGTH = 6
DEFAULT_OTP_TTL_SECONDS = 120

OTP_SESSION_KEY = "otp_verification"

# ---------------------------------------------------------------- آواتار
# واحد: بایت. (۲ مگابایت)
AVATAR_MAX_SIZE = 2 * 1024 * 1024

# پسوندهای مجاز در core/validators.py با این مجموعه سنجیده میشوند
AVATAR_ALLOWED_CONTENT_TYPES = frozenset({
    "image/jpeg",
    "image/png",
    "image/webp",
})

# context_processors.py
"""
Context processorهای عمومی پروژه Shine Shop.

شامل:
- شمارنده سبد خرید
- شمارنده لیست علاقه‌مندی
- اطلاعات عمومی فروشگاه
- اطلاعات تماس و آدرس
- لینک‌های شبکه‌های اجتماعی
- سال جاری

شمارنده‌ها برای کاهش تعداد Queryهای دیتابیس در cache نگهداری می‌شوند.
"""

from __future__ import annotations

import logging
from typing import Any, Callable

from django.conf import settings
from django.core.cache import cache
from django.db.models import Count, Sum
from django.utils import timezone

logger = logging.getLogger(__name__)

# ============================================================================
# Cache Configuration
# ============================================================================

COUNTER_CACHE_TIMEOUT = getattr(
    settings,
    "SITE_COUNTER_CACHE_TIMEOUT",
    300,
)

CART_COUNT_KEY = "site_counters:cart:{user_id}"

WISHLIST_COUNT_KEY = "site_counters:wishlist:{user_id}"


# ============================================================================
# Cart Counter
# ============================================================================


def _load_cart_count(user_id: int) -> int:
    """تعداد کل اقلام موجود در سبد خرید فعال کاربر."""

    # Import محلی برای جلوگیری از circular import
    # هنگام بالا آمدن Django.
    from cart.models import Cart

    queryset = Cart.objects.filter(
        user_id=user_id,
    )

    # اگر مدل Cart فیلد is_active داشته باشد،
    # فقط سبد فعال را در نظر می‌گیریم.
    if hasattr(Cart, "is_active"):
        queryset = queryset.filter(
            is_active=True,
        )

    total = queryset.aggregate(
        total=Sum("items__quantity"),
    )["total"]

    return int(total or 0)


# ============================================================================
# Wishlist Counter
# ============================================================================


def _load_wishlist_count(user_id: int) -> int:
    """تعداد آیتم‌های لیست علاقه‌مندی فعال کاربر."""

    # Import محلی برای جلوگیری از circular import.
    from wishlist.models import Wishlist

    queryset = Wishlist.objects.filter(
        user_id=user_id,
    )

    # اگر مدل Wishlist فیلد is_active داشته باشد،
    # فقط موارد فعال شمارش می‌شوند.
    if hasattr(Wishlist, "is_active"):
        queryset = queryset.filter(
            is_active=True,
        )

    total = queryset.aggregate(
        total=Count("items"),
    )["total"]

    return int(total or 0)


# ============================================================================
# Cached Counter
# ============================================================================


def _cached_counter(
        key: str,
        loader: Callable[[], int],
) -> int:
    """
    شمارنده را از cache می‌خواند.

    اگر مقدار در cache وجود نداشته باشد، loader اجرا می‌شود.
    خطای cache یا database نباید باعث HTTP 500 شدن کل سایت شود.
    """

    # ------------------------------------------------------------------------
    # Read from cache
    # ------------------------------------------------------------------------

    try:
        value = cache.get(key)
    except Exception:  # noqa: BLE001
        logger.exception(
            "خطا در خواندن cache شمارنده: %s",
            key,
        )
        value = None

    if value is not None:
        try:
            return int(value)
        except (TypeError, ValueError):
            logger.warning(
                "مقدار نامعتبر در cache شمارنده: %s",
                key,
            )

    # ------------------------------------------------------------------------
    # Calculate counter
    # ------------------------------------------------------------------------

    try:
        value = loader()
    except Exception:  # noqa: BLE001
        logger.exception(
            "خطا در محاسبه شمارنده: %s",
            key,
        )
        return 0

    # ------------------------------------------------------------------------
    # Save to cache
    # ------------------------------------------------------------------------

    try:
        cache.set(
            key,
            value,
            COUNTER_CACHE_TIMEOUT,
        )
    except Exception:  # noqa: BLE001
        logger.exception(
            "خطا در ذخیره شمارنده در cache: %s",
            key,
        )

    return int(value)


# ============================================================================
# Cache Invalidation
# ============================================================================


def invalidate_site_counters(
        user_id: int | None,
) -> None:
    """
    cache شمارنده‌های یک کاربر را پاک می‌کند.

    این تابع را بعد از هر تغییر در Cart یا Wishlist صدا بزنید.

    مثال:

        from core.context_processors import invalidate_site_counters

        invalidate_site_counters(user_id)
    """

    if not user_id:
        return

    keys = [
        CART_COUNT_KEY.format(
            user_id=user_id,
        ),
        WISHLIST_COUNT_KEY.format(
            user_id=user_id,
        ),
    ]

    try:
        cache.delete_many(keys)
    except Exception:  # noqa: BLE001
        logger.exception(
            "خطا در پاک کردن cache شمارنده‌ها برای user_id=%s",
            user_id,
        )


# ============================================================================
# Site Counters Context Processor
# ============================================================================


def site_counters(request) -> dict[str, int]:
    """
    تعداد اقلام سبد خرید و علاقه‌مندی را برای Templateها فراهم می‌کند.

    کاربران مهمان همیشه مقدار صفر دریافت می‌کنند.
    """

    user = getattr(
        request,
        "user",
        None,
    )

    if user is None:
        return {
            "cart_count": 0,
            "wishlist_count": 0,
        }

    if not getattr(
            user,
            "is_authenticated",
            False,
    ):
        return {
            "cart_count": 0,
            "wishlist_count": 0,
        }

    user_id = getattr(
        user,
        "pk",
        None,
    )

    if not user_id:
        return {
            "cart_count": 0,
            "wishlist_count": 0,
        }

    return {
        "cart_count": _cached_counter(
            CART_COUNT_KEY.format(
                user_id=user_id,
            ),
            lambda: _load_cart_count(user_id),
        ),

        "wishlist_count": _cached_counter(
            WISHLIST_COUNT_KEY.format(
                user_id=user_id,
            ),
            lambda: _load_wishlist_count(user_id),
        ),
    }


# ============================================================================
# Current Year
# ============================================================================


def _current_year() -> int:
    """
    سال جاری را برمی‌گرداند.

    در صورت نصب بودن jdatetime، سال شمسی برگردانده می‌شود.
    در غیر این صورت سال میلادی استفاده خواهد شد.
    """

    try:
        import jdatetime
    except ImportError:
        return timezone.localdate().year

    return jdatetime.date.today().year


# ============================================================================
# Site Information
# ============================================================================


def site_info(request) -> dict[str, Any]:
    """
    اطلاعات پایه فروشگاه را برای Templateها فراهم می‌کند.

    کاربردها:
    - Header
    - Footer
    - صفحه تماس با ما
    - SEO
    - Structured Data
    """

    instagram_url = getattr(
        settings,
        "SITE_INSTAGRAM_URL",
        "",
    )

    telegram_url = getattr(
        settings,
        "SITE_TELEGRAM_URL",
        "",
    )

    social_links = [
        link
        for link in (
            instagram_url,
            telegram_url,
        )
        if link
    ]

    address_parts = [
        part
        for part in (
            getattr(
                settings,
                "SITE_STREET",
                "",
            ),
            getattr(
                settings,
                "SITE_CITY",
                "",
            ),
            getattr(
                settings,
                "SITE_REGION",
                "",
            ),
        )
        if part
    ]

    return {
        # --------------------------------------------------------------------
        # Store
        # --------------------------------------------------------------------

        "site_name": getattr(
            settings,
            "SITE_NAME",
            "",
        ),

        "site_phone": getattr(
            settings,
            "SITE_PHONE",
            "",
        ),

        "site_email": getattr(
            settings,
            "SITE_EMAIL",
            "",
        ),

        # --------------------------------------------------------------------
        # Address
        # --------------------------------------------------------------------

        "site_street": getattr(
            settings,
            "SITE_STREET",
            "",
        ),

        "site_city": getattr(
            settings,
            "SITE_CITY",
            "",
        ),

        "site_region": getattr(
            settings,
            "SITE_REGION",
            "",
        ),

        "site_country": getattr(
            settings,
            "SITE_COUNTRY",
            "",
        ),

        "site_address_full": "، ".join(
            address_parts,
        ),

        # --------------------------------------------------------------------
        # Social
        # --------------------------------------------------------------------

        "site_instagram": instagram_url,

        "site_telegram": telegram_url,

        "site_social_links": social_links,

        # --------------------------------------------------------------------
        # Date
        # --------------------------------------------------------------------

        "current_year": _current_year(),
    }

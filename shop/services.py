# shop/services.py
from django.db.models import QuerySet

from products.models import Product

from .selectors import get_shop_products


class ShopService:
    """سرویس فروشگاه — لایه‌ی واسط بین ویو و سلکتورها."""

    @staticmethod
    def filter_products(
            *,
            query: str = "",
            category_slug: str = "",
            brand_slug: str = "",
            sort: str = "",
    ) -> QuerySet[Product]:
        return get_shop_products(
            query=query.strip(),
            category_slug=category_slug.strip(),
            brand_slug=brand_slug.strip(),
            sort=sort.strip(),
        )

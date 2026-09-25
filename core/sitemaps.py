"""نقشهٔ سایت (sitemap.xml) برای Shine Shop."""

from __future__ import annotations

from typing import Any

from django.conf import settings
from django.contrib.sitemaps import Sitemap
from django.urls import NoReverseMatch, reverse

from products.models import Category, Product


class BaseSitemap(Sitemap):
    """تنظیمات مشترک تمام Sitemapهای پروژه."""

    protocol = "http" if settings.DEBUG else "https"
    limit = 5000


class ProductSitemap(BaseSitemap):
    """نقشهٔ سایت محصولات قابل نمایش."""

    changefreq = "daily"
    priority = 0.9

    def items(self):
        """محصولات فعال/قابل فروش را برمی‌گرداند."""
        queryset = Product.objects.all()

        if hasattr(Product, "is_available"):
            queryset = queryset.filter(is_available=True)

        if hasattr(Product, "is_active"):
            queryset = queryset.filter(is_active=True)

        fields = ["slug"]

        if hasattr(Product, "updated_at"):
            fields.append("updated_at")

        return queryset.only(*fields)

    def lastmod(self, obj: Any):
        """آخرین زمان به‌روزرسانی محصول."""
        return getattr(obj, "updated_at", None)

    def location(self, obj: Any) -> str:
        """آدرس صفحهٔ محصول."""
        return obj.get_absolute_url()


class CategorySitemap(BaseSitemap):
    """نقشهٔ سایت دسته‌بندی‌های فعال."""

    changefreq = "weekly"
    priority = 0.7

    def items(self):
        """دسته‌بندی‌های فعال را برمی‌گرداند."""
        queryset = Category.objects.all()

        if hasattr(Category, "is_active"):
            queryset = queryset.filter(is_active=True)

        fields = ["slug"]

        if hasattr(Category, "updated_at"):
            fields.append("updated_at")

        return queryset.only(*fields)

    def lastmod(self, obj: Any):
        """آخرین زمان به‌روزرسانی دسته‌بندی."""
        return getattr(obj, "updated_at", None)

    def location(self, obj: Any) -> str:
        """آدرس صفحهٔ دسته‌بندی."""
        return obj.get_absolute_url()


class StaticViewSitemap(BaseSitemap):
    """نقشهٔ سایت صفحات ثابت پروژه."""

    changefreq = "weekly"
    priority = 0.5

    # فقط URLهایی که واقعاً در urls.py ثبت شده‌اند
    # وارد sitemap می‌شوند.
    URL_NAMES = (
        "shop:home",
        "products:list",
    )

    def items(self) -> list[str]:
        """نام URLهای موجود را پیدا می‌کند."""
        available: list[str] = []

        for name in self.URL_NAMES:
            try:
                reverse(name)
            except NoReverseMatch:
                continue

            available.append(name)

        return available

    def location(self, item: str) -> str:
        """آدرس صفحهٔ ثابت."""
        return reverse(item)


sitemaps = {
    "products": ProductSitemap,
    "categories": CategorySitemap,
    "static": StaticViewSitemap,
}

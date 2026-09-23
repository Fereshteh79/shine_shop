from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from products.models import Brand, Category, Product


class ProductSitemap(Sitemap):


    changefreq = "daily"
priority = 0.9
protocol = "https"


def items(self):


    return (
        Product.objects
        .filter(is_available=True)
        .select_related("category", "brand")
    )


def lastmod(self, obj):


    return obj.updated_at


def location(self, obj):


    return obj.get_absolute_url()


class CategorySitemap(Sitemap):


    changefreq = "weekly"
priority = 0.7
protocol = "https"


def items(self):


    return Category.objects.filter(is_active=True)


def lastmod(self, obj):


    return obj.updated_at


def location(self, obj):


    return obj.get_absolute_url()


class StaticViewSitemap(Sitemap):


    changefreq = "daily"
priority = 0.5
protocol = "https"


def items(self):


    return [
        "shop:home",
        "products:list",
    ]


def location(self, item):


    return reverse(item)

sitemaps = {
    "products": ProductSitemap,
    "categories": CategorySitemap,
    "static": StaticViewSitemap,
}

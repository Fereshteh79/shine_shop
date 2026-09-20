from django.db.models import Q, QuerySet

from products.models import Brand, Category, Product

SORT_OPTIONS = {
    "newest": "-created_at",
    "oldest": "created_at",
    "price_low": "price",
    "price_high": "-price",
    "name": "name",
}

DEFAULT_SORT = "-created_at"


def get_home_products() -> QuerySet[Product]:
    """محصولات منتخب صفحه اصلی."""
    return (
        Product.objects
        .filter(is_available=True, is_featured=True)
        .select_related("category", "brand")
        .prefetch_related("images")
        .order_by("-created_at")[:12]
    )


def get_shop_products(
        *,
        query: str = "",
        category_slug: str = "",
        brand_slug: str = "",
        sort: str = "",
) -> QuerySet[Product]:
    """لیست محصولات فروشگاه با فیلتر و مرتب‌سازی بهینه."""
    products = (
        Product.objects
        .filter(is_available=True)
        .select_related("category", "brand")
        .prefetch_related("images")
    )

    if query:
        # جستجو فقط روی فیلدهای سبک و ایندکس‌پذیر
        # (جستجوی icontains روی description طولانی سنگین است)
        products = products.filter(
            Q(name__icontains=query)
            | Q(short_description__icontains=query)
            | Q(sku__icontains=query)
            | Q(brand__name__icontains=query)
        )

    if category_slug:
        products = products.filter(category__slug=category_slug)

    if brand_slug:
        products = products.filter(brand__slug=brand_slug)

    return products.order_by(SORT_OPTIONS.get(sort, DEFAULT_SORT))


def get_active_categories() -> QuerySet[Category]:
    return (
        Category.objects
        .filter(is_active=True)
        .order_by("name")
    )


def get_active_brands() -> QuerySet[Brand]:
    return (
        Brand.objects
        .filter(is_active=True)
        .order_by("name")
    )


def get_category(slug: str) -> Category | None:
    return Category.objects.filter(slug=slug, is_active=True).first()

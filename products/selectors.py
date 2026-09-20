from django.db.models import Prefetch, Q, QuerySet

from .models import Product, ProductImage

SORT_OPTIONS = {
    "newest": "-created_at",
    "oldest": "created_at",
    "price_low": "price",
    "price_high": "-price",
    "name": "name",
}

DEFAULT_SORT = "-created_at"


def images_ordered():
    return ProductImage.objects.order_by("sort_order", "id")


def product_queryset() -> QuerySet[Product]:
    """کوئری‌ست پایه بهینه — بدون N+1."""
    return (
        Product.objects
        .select_related("category", "brand")
        .prefetch_related(
            Prefetch("images", queryset=images_ordered()),
            "variants",
            "attributes",
        )
    )


def get_available_products(*, sort: str = "") -> QuerySet[Product]:
    return (
        Product.objects
        .filter(is_available=True)
        .select_related("category", "brand")
        .prefetch_related(
            Prefetch("images", queryset=images_ordered()),
        )
        .order_by(SORT_OPTIONS.get(sort, DEFAULT_SORT))
    )


def get_featured_products(*, limit: int = 12) -> QuerySet[Product]:
    return (
        Product.objects
        .filter(is_available=True, is_featured=True)
        .select_related("category", "brand")
        .prefetch_related(Prefetch("images", queryset=images_ordered()))
        .order_by("-created_at")[:limit]
    )


def get_product_by_slug(slug: str) -> Product | None:
    return get_product_detail(slug)


def get_product_detail(slug: str) -> Product | None:
    """جزئیات کامل محصول با تمام روابط مرتبط."""
    return (
        Product.objects
        .filter(slug=slug, is_available=True)
        .select_related("category", "brand")
        .prefetch_related(
            Prefetch("images", queryset=images_ordered()),
            "variants",
            "attributes",
        )
        .first()
    )


def get_related_products(*, product: Product, limit: int = 4) -> QuerySet[Product]:
    """محصولات مشابه از همان دسته‌بندی."""
    return (
        Product.objects
        .filter(
            is_available=True,
            category=product.category,
        )
        .exclude(pk=product.pk)
        .select_related("category", "brand")
        .prefetch_related(Prefetch("images", queryset=images_ordered()))
        .order_by("-is_featured", "-created_at")[:limit]
    )


def search_products(query: str) -> QuerySet[Product]:
    queryset = (
        Product.objects
        .filter(is_available=True)
        .select_related("category", "brand")
        .prefetch_related(Prefetch("images", queryset=images_ordered()))
    )

    if not query:
        return queryset.order_by(DEFAULT_SORT)

    return (
        queryset
        .filter(
            Q(name__icontains=query)
            | Q(sku__icontains=query)
            | Q(short_description__icontains=query)
            | Q(brand__name__icontains=query)
            | Q(category__name__icontains=query)
        )
        .distinct()
        .order_by(DEFAULT_SORT)
    )

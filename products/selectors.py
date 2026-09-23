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


def ordered_images():
    return ProductImage.objects.order_by(
        "sort_order",
        "id",
    )


def product_queryset() -> QuerySet[Product]:
    """
    QuerySet پایه برای نمایش کامل محصول.
    """

    return (
        Product.objects
        .select_related(
            "category",
            "brand",
        )
        .prefetch_related(
            Prefetch(
                "images",
                queryset=ordered_images(),
            ),
            "variants",
            "attributes",
        )
    )


def available_product_queryset() -> QuerySet[Product]:
    """
    فقط محصولات قابل فروش.
    """

    return (
        product_queryset()
        .filter(is_available=True)
    )


def get_available_products(
        *,
        sort: str = "newest",
) -> QuerySet[Product]:
    return (
        available_product_queryset()
        .order_by(
            SORT_OPTIONS.get(
                sort,
                DEFAULT_SORT,
            )
        )
    )


def get_featured_products(
        *,
        limit: int = 12,
) -> QuerySet[Product]:
    return (
        available_product_queryset()
        .filter(is_featured=True)
        .order_by(
            "-created_at",
        )[:limit]
    )


def get_product_detail(
        slug: str,
) -> Product | None:
    return (
        available_product_queryset()
        .filter(slug=slug)
        .first()
    )


def get_product_by_slug(
        slug: str,
) -> Product | None:
    return get_product_detail(slug)


def get_related_products(
        *,
        product: Product,
        limit: int = 4,
) -> QuerySet[Product]:
    return (
        Product.objects
        .filter(
            is_available=True,
            category_id=product.category_id,
        )
        .exclude(pk=product.pk)
        .select_related(
            "category",
            "brand",
        )
        .prefetch_related(
            Prefetch(
                "images",
                queryset=ordered_images(),
            ),
        )
        .order_by(
            "-is_featured",
            "-created_at",
        )[:limit]
    )


def search_products(
        query: str,
) -> QuerySet[Product]:
    queryset = available_product_queryset()

    query = query.strip()

    if not query:
        return queryset.order_by(
            DEFAULT_SORT,
        )

    return (
        queryset
        .filter(
            Q(name__icontains=query)
            | Q(sku__icontains=query)
            | Q(short_description__icontains=query)
            | Q(description__icontains=query)
            | Q(brand__name__icontains=query)
            | Q(category__name__icontains=query)
        )
        .distinct()
        .order_by(
            DEFAULT_SORT,
        )
    )

from __future__ import annotations

from django.db.models import Prefetch
from rest_framework import generics
from rest_framework.permissions import AllowAny

from .models import (
    Product,
    ProductAttribute,
    ProductImage,
    ProductVariant,
)
from .serializers import (
    ProductDetailSerializer,
    ProductListSerializer,
)


class ProductBaseAPIView:
    """
    تنظیمات مشترک API محصولات.

    این API برای نمایش محصولات فروشگاه است؛
    بنابراین endpointهای آن عمومی هستند.
    """

    permission_classes = (AllowAny,)

    def get_product_queryset(self):
        """
        QuerySet اصلی محصولات.

        روابط مستقیم با select_related و روابط چندتایی
        با prefetch_related بارگذاری می‌شوند تا از N+1 query
        جلوگیری شود.
        """

        images_queryset = (
            ProductImage.objects
            .only(
                "id",
                "product_id",
                "image",
                "alt_text",
                "is_primary",
                "sort_order",
            )
            .order_by("sort_order", "id")
        )

        variants_queryset = (
            ProductVariant.objects
            .select_related("product")
            .only(
                "id",
                "product_id",
                "name",
                "sku",
                "price",
                "stock",
                "is_active",
                "product__id",
                "product__price",
                "product__discount_price",
                "product__is_available",
            )
            .order_by("id")
        )

        attributes_queryset = (
            ProductAttribute.objects
            .only(
                "id",
                "product_id",
                "name",
                "value",
            )
            .order_by("id")
        )

        return (
            Product.objects
            .filter(is_available=True)
            .select_related(
                "category",
                "brand",
            )
            .prefetch_related(
                Prefetch(
                    "images",
                    queryset=images_queryset,
                ),
                Prefetch(
                    "variants",
                    queryset=variants_queryset,
                ),
                Prefetch(
                    "attributes",
                    queryset=attributes_queryset,
                ),
            )
        )


class ProductAPIListView(
    ProductBaseAPIView,
    generics.ListAPIView,
):
    """
    API لیست محصولات قابل فروش.

    GET /products/api/
    """

    serializer_class = ProductListSerializer

    def get_queryset(self):
        return self.get_product_queryset()


class ProductAPIDetailView(
    ProductBaseAPIView,
    generics.RetrieveAPIView,
):
    """
    API جزئیات یک محصول.

    محصول با slug دریافت می‌شود.

    GET /products/api/<slug>/
    """

    serializer_class = ProductDetailSerializer
    lookup_field = "slug"
    lookup_url_kwarg = "slug"

    def get_queryset(self):
        return self.get_product_queryset()

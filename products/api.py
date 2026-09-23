from rest_framework import generics

from .models import Product
from .serializers import (
    ProductDetailSerializer,
    ProductListSerializer,
)


class ProductAPIListView(generics.ListAPIView):
    serializer_class = ProductListSerializer

    def get_queryset(self):
        return (
            Product.objects
            .filter(is_available=True)
            .select_related(
                "category",
                "brand",
            )
            .prefetch_related(
                "images",
                "variants",
                "attributes",
            )
        )


class ProductAPIDetailView(generics.RetrieveAPIView):
    serializer_class = ProductDetailSerializer
    lookup_field = "slug"

    def get_queryset(self):
        return (
            Product.objects
            .filter(is_available=True)
            .select_related(
                "category",
                "brand",
            )
            .prefetch_related(
                "images",
                "variants",
                "attributes",
            )
        )

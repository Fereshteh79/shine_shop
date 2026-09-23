from rest_framework import serializers

from .models import (
    Product,
    ProductAttribute,
    ProductImage,
    ProductVariant,
)


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = (
            "image",
            "alt_text",
            "is_primary",
            "sort_order",
        )


class ProductVariantSerializer(serializers.ModelSerializer):
    final_price = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = ProductVariant
        fields = (
            "id",
            "name",
            "sku",
            "price",
            "final_price",
            "stock",
            "is_active",
        )


class ProductAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductAttribute
        fields = (
            "name",
            "value",
        )


class ProductListSerializer(serializers.ModelSerializer):
    final_price = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        read_only=True,
    )

    seo_title = serializers.CharField(
        read_only=True,
    )

    seo_description = serializers.CharField(
        read_only=True,
    )

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "slug",
            "sku",
            "short_description",
            "price",
            "discount_price",
            "final_price",
            "stock",
            "is_available",
            "is_featured",
            "seo_title",
            "seo_description",
        )


class ProductDetailSerializer(ProductListSerializer):
    images = ProductImageSerializer(
        many=True,
        read_only=True,
    )

    variants = ProductVariantSerializer(
        many=True,
        read_only=True,
    )

    attributes = ProductAttributeSerializer(
        many=True,
        read_only=True,
    )

    category = serializers.StringRelatedField()
    brand = serializers.StringRelatedField(
        allow_null=True,
    )

    class Meta(ProductListSerializer.Meta):
        fields = ProductListSerializer.Meta.fields + (
            "category",
            "brand",
            "description",
            "images",
            "variants",
            "attributes",
        )

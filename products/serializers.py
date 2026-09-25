from __future__ import annotations

from rest_framework import serializers

from .models import (
    Product,
    ProductAttribute,
    ProductImage,
    ProductVariant,
)


class ProductImageSerializer(serializers.ModelSerializer):
    """
    Serializer مربوط به تصاویر محصول.
    """

    class Meta:
        model = ProductImage

        fields = (
            "image",
            "alt_text",
            "is_primary",
            "sort_order",
        )

        read_only_fields = fields


class ProductVariantSerializer(serializers.ModelSerializer):
    """
    Serializer مربوط به تنوع‌های محصول.
    """

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

        read_only_fields = fields


class ProductAttributeSerializer(serializers.ModelSerializer):
    """
    Serializer مربوط به ویژگی‌های محصول.
    """

    class Meta:
        model = ProductAttribute

        fields = (
            "name",
            "value",
        )

        read_only_fields = fields


class ProductListSerializer(serializers.ModelSerializer):
    """
    Serializer سبک برای لیست محصولات.

    اطلاعات سنگین مثل تصاویر، تنوع‌ها و ویژگی‌ها
    در لیست ارسال نمی‌شوند.
    """

    final_price = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        read_only=True,
    )

    has_discount = serializers.BooleanField(
        read_only=True,
    )

    discount_percentage = serializers.IntegerField(
        read_only=True,
    )

    in_stock = serializers.BooleanField(
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
            "has_discount",
            "discount_percentage",
            "stock",
            "in_stock",
            "is_available",
            "is_featured",
            "seo_title",
            "seo_description",
        )

        read_only_fields = fields


class ProductDetailSerializer(ProductListSerializer):
    """
    Serializer کامل صفحه جزئیات محصول.
    """

    category = serializers.StringRelatedField()

    brand = serializers.StringRelatedField(
        allow_null=True,
    )

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

    class Meta(ProductListSerializer.Meta):
        fields = ProductListSerializer.Meta.fields + (
            "category",
            "brand",
            "description",
            "images",
            "variants",
            "attributes",
        )

        read_only_fields = fields

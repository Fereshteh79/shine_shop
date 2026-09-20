from django.contrib import admin

from .models import (
    Brand,
    Category,
    Product,
    ProductAttribute,
    ProductImage,
    ProductVariant,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ("is_active",)


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ("is_active",)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0
    fields = ("image", "alt_text", "is_primary", "sort_order")


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0
    fields = ("name", "sku", "price", "stock", "is_active")


class ProductAttributeInline(admin.TabularInline):
    model = ProductAttribute
    extra = 0
    fields = ("name", "value")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form_fieldsets = None

    list_display = (
        "name",
        "sku",
        "category",
        "brand",
        "price",
        "discount_price",
        "stock",
        "is_available",
        "is_featured",
        "created_at",
    )
    list_filter = ("is_available", "is_featured", "category", "brand", "created_at")
    search_fields = ("name", "sku", "slug", "short_description")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at")
    list_editable = ("is_available", "is_featured", "stock")
    list_per_page = 25
    ordering = ("-created_at",)
    inlines = (ProductImageInline, ProductVariantInline, ProductAttributeInline)

    fieldsets = (
        ("اطلاعات اصلی", {
            "fields": ("category", "brand", "name", "slug", "sku"),
        }),
        ("توضیحات", {
            "fields": ("short_description", "description"),
        }),
        ("قیمت و موجودی", {
            "fields": ("price", "discount_price", "stock"),
        }),
        ("وضعیت", {
            "fields": ("is_available", "is_featured"),
        }),
        ("سئو", {
            "classes": ("collapse",),
            "fields": ("meta_title", "meta_description"),
        }),
        ("تاریخ‌ها", {
            "classes": ("collapse",),
            "fields": ("created_at", "updated_at"),
        }),
    )


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("product", "is_primary", "sort_order")
    list_filter = ("is_primary",)
    search_fields = ("product__name", "product__sku", "alt_text")


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ("product", "name", "sku", "price", "stock", "is_active")
    list_filter = ("is_active",)
    search_fields = ("product__name", "sku", "name")


@admin.register(ProductAttribute)
class ProductAttributeAdmin(admin.ModelAdmin):
    list_display = ("product", "name", "value")
    search_fields = ("product__name", "name", "value")

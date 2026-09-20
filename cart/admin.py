from django.contrib import admin

from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    fields = ("product", "variant", "quantity")
    autocomplete_fields = ("product", "variant")


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "total_items",
        "subtotal",
        "created_at",
        "updated_at",
    )
    search_fields = (
        "user__username",
        "user__email",
        "user__phone_number",
    )
    readonly_fields = ("created_at", "updated_at")
    inlines = (CartItemInline,)


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = (
        "cart",
        "product",
        "variant",
        "quantity",
        "line_total",
        "created_at",
    )
    search_fields = (
        "cart__user__username",
        "product__name",
        "product__sku",
    )
    list_filter = ("created_at",)
    autocomplete_fields = ("product", "variant")

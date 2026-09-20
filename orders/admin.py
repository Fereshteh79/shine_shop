from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

    fields = (
        "product",
        "variant",
        "product_name",
        "variant_name",
        "sku",
        "quantity",
        "unit_price",
        "total_price",
    )

    readonly_fields = fields


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "status",
        "total_amount",
        "recipient_name",
        "city",
        "payment_expires_at",
        "created_at",
    )

    list_filter = (
        "status",
        "created_at",
    )

    search_fields = (
        "id",
        "user__username",
        "user__email",
        "recipient_name",
        "phone_number",
        "postal_code",
    )

    readonly_fields = (
        "subtotal",
        "shipping_cost",
        "discount_amount",
        "total_amount",
        "created_at",
        "updated_at",
    )

    inlines = (
        OrderItemInline,
    )

    ordering = (
        "-created_at",
    )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "product_name",
        "variant_name",
        "quantity",
        "unit_price",
        "total_price",
    )

    search_fields = (
        "product_name",
        "sku",
        "order__id",
    )

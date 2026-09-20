from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "transaction_id",
        "order",
        "user",
        "amount",
        "gateway",
        "status",
        "reference_id",
        "created_at",
        "paid_at",
    )

    list_filter = (
        "status",
        "gateway",
        "created_at",
    )

    search_fields = (
        "transaction_id",
        "authority",
        "reference_id",
        "order__id",
        "user__username",
        "user__email",
    )

    readonly_fields = (
        "transaction_id",
        "authority",
        "reference_id",
        "gateway_response",
        "created_at",
        "updated_at",
        "paid_at",
    )

    ordering = (
        "-created_at",
    )

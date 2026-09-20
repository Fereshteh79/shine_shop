from django.contrib import admin

from .models import Wishlist, WishlistItem


class WishlistItemInline(admin.TabularInline):
    model = WishlistItem
    extra = 0
    fields = (
        "product",
        "created_at",
    )
    readonly_fields = (
        "created_at",
    )


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "user__username",
        "user__email",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    inlines = (
        WishlistItemInline,
    )


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = (
        "wishlist",
        "product",
        "created_at",
    )

    search_fields = (
        "wishlist__user__username",
        "product__name",
        "product__sku",
    )

    readonly_fields = (
        "created_at",
    )

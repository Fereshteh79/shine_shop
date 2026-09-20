from django.db.models import Prefetch

from products.models import ProductImage

from .models import Cart, CartItem


def items_ordered():
    return (
        CartItem.objects
        .select_related("product", "product__brand", "variant")
        .prefetch_related(
            Prefetch(
                "product__images",
                queryset=ProductImage.objects.order_by(
                    "-is_primary", "sort_order", "id",
                ),
            ),
        )
    )


def get_user_cart(user) -> Cart | None:
    """سبد کاربر با آیتم‌های کاملاً prefetch شده — بدون N+1."""
    return (
        Cart.objects
        .filter(user=user)
        .prefetch_related(
            Prefetch("items", queryset=items_ordered()),
        )
        .first()
    )


def get_or_create_user_cart(user) -> Cart:
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart

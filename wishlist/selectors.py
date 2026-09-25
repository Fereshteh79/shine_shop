from django.db.models import Prefetch

from .models import Wishlist, WishlistItem


def get_or_create_user_wishlist(user):
    wishlist, _ = Wishlist.objects.get_or_create(user=user)
    return wishlist


def get_user_wishlist(user):
    return (
        Wishlist.objects
        .filter(user=user)
        .prefetch_related(
            Prefetch(
                "items",
                queryset=WishlistItem.objects.select_related(
                    "product", "product__category", "product__brand",
                ),
            ),
        )
        .first()
    )


def get_wishlist_products(user):
    wishlist = get_user_wishlist(user)

    if wishlist is None:
        return []

    return [
        item.product
        for item in wishlist.items.all()
    ]


def is_product_in_wishlist(*, user, product):
    return Wishlist.objects.filter(
        user=user,
        items__product=product,
    ).exists()

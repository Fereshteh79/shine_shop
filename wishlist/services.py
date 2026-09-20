from django.db import transaction

from core.exceptions import ValidationError

from .models import Wishlist, WishlistItem


class WishlistService:

    @staticmethod
    @transaction.atomic
    def add_product(*, user, product):
        wishlist, _ = Wishlist.objects.get_or_create(
            user=user,
        )

        item, created = WishlistItem.objects.get_or_create(
            wishlist=wishlist,
            product=product,
        )

        return item, created

    @staticmethod
    @transaction.atomic
    def remove_product(*, user, product):
        wishlist = (
            Wishlist.objects
            .filter(user=user)
            .first()
        )

        if wishlist is None:
            return False

        deleted, _ = WishlistItem.objects.filter(
            wishlist=wishlist,
            product=product,
        ).delete()

        return deleted > 0

    @staticmethod
    @transaction.atomic
    def toggle_product(*, user, product):
        wishlist, _ = Wishlist.objects.get_or_create(
            user=user,
        )

        item = WishlistItem.objects.filter(
            wishlist=wishlist,
            product=product,
        ).first()

        if item:
            item.delete()
            return False

        WishlistItem.objects.create(
            wishlist=wishlist,
            product=product,
        )
        return True

    @staticmethod
    @transaction.atomic
    def clear(*, user):
        wishlist = (
            Wishlist.objects
            .filter(user=user)
            .first()
        )

        if wishlist is None:
            return

        wishlist.items.all().delete()

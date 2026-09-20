from django.db import transaction
from django.shortcuts import get_object_or_404

from core.exceptions import InsufficientStockError, ValidationError
from products.models import Product, ProductVariant

from .models import Cart, CartItem


class StockChecker:
    """بررسی موجودی محصول یا تنوع — برای حذف تکرار بین متدها."""

    @staticmethod
    def get_stock(item: Product | ProductVariant, *, variant: bool) -> int:
        return item.stock

    @staticmethod
    def validate_available(item, *, variant: bool) -> None:
        if variant:
            if not item.is_active or not item.in_stock:
                raise InsufficientStockError("این تنوع محصول دیگر موجود نیست.")
        else:
            if not item.is_available or not item.in_stock:
                raise InsufficientStockError("این محصول دیگر موجود نیست.")

    @staticmethod
    def validate_quantity(item, quantity: int, *, variant: bool) -> None:
        if quantity > item.stock:
            raise InsufficientStockError(
                "موجودی این تنوع محصول کافی نیست."
                if variant
                else "موجودی محصول کافی نیست."
            )


class CartService:

    @staticmethod
    @transaction.atomic
    def get_or_create_cart(*, user) -> Cart:
        cart, _ = Cart.objects.get_or_create(user=user)
        return cart

    @staticmethod
    def _current_quantity(cart: Cart, product: Product, variant) -> int:
        return (
                CartItem.objects
                .filter(cart=cart, product=product, variant=variant)
                .values_list("quantity", flat=True)
                .first()
                or 0
        )

    @staticmethod
    @transaction.atomic
    def add_item(
            *,
            user,
            product_id: int,
            quantity: int = 1,
            variant_id: int | None = None,
    ) -> CartItem:
        if quantity <= 0:
            raise ValidationError("تعداد باید بیشتر از صفر باشد.")

        cart = CartService.get_or_create_cart(user=user)
        cart = Cart.objects.select_for_update().get(pk=cart.pk)

        product = get_object_or_404(
            Product.objects.select_for_update(),
            pk=product_id,
            is_available=True,
        )

        active_variants_exist = ProductVariant.objects.filter(
            product_id=product.id,
            is_active=True,
        ).exists()

        if active_variants_exist and variant_id is None:
            raise ValidationError("لطفاً ابتدا تنوع محصول را انتخاب کنید.")

        variant = None

        if variant_id is not None:
            variant = get_object_or_404(
                ProductVariant.objects.select_for_update(),
                pk=variant_id,
                product_id=product.id,
                is_active=True,
            )
            StockChecker.validate_available(variant, variant=True)
            stock_target = variant
        else:
            StockChecker.validate_available(product, variant=False)
            stock_target = product

        current = CartService._current_quantity(cart, product, variant)
        StockChecker.validate_quantity(
            stock_target, current + quantity, variant=bool(variant),
        )

        item, created = (
            CartItem.objects
            .select_for_update()
            .get_or_create(
                cart=cart,
                product=product,
                variant=variant,
                defaults={"quantity": quantity},
            )
        )

        if not created:
            item.quantity = current + quantity
            item.save(update_fields=["quantity", "updated_at"])

        cart.save(update_fields=["updated_at"])
        return item

    @staticmethod
    @transaction.atomic
    def update_item(*, user, item_id: int, quantity: int) -> CartItem:
        if quantity <= 0:
            raise ValidationError("تعداد باید بیشتر از صفر باشد.")

        item = get_object_or_404(
            CartItem.objects
            .select_for_update()
            .select_related("cart", "product", "variant"),
            pk=item_id,
            cart__user=user,
        )

        if item.variant_id:
            target = ProductVariant.objects.select_for_update().get(
                pk=item.variant_id,
            )
            StockChecker.validate_available(target, variant=True)
        else:
            target = Product.objects.select_for_update().get(
                pk=item.product_id,
            )
            StockChecker.validate_available(target, variant=False)

        StockChecker.validate_quantity(target, quantity, variant=bool(item.variant_id))

        item.quantity = quantity
        item.save(update_fields=["quantity", "updated_at"])
        return item

    @staticmethod
    @transaction.atomic
    def remove_item(*, user, item_id: int) -> None:
        item = get_object_or_404(
            CartItem.objects.select_for_update(),
            pk=item_id,
            cart__user=user,
        )
        item.delete()

    @staticmethod
    @transaction.atomic
    def clear_cart(*, user) -> None:
        cart = Cart.objects.filter(user=user).first()

        if cart:
            cart.items.all().delete()
            cart.save(update_fields=["updated_at"])

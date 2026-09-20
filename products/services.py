from django.db import transaction
from django.shortcuts import get_object_or_404

from core.exceptions import InsufficientStockError, ValidationError

from .models import Product, ProductImage, ProductVariant


class ProductService:

    @staticmethod
    @transaction.atomic
    def create_product(*, data: dict) -> Product:
        return Product.objects.create(**data)

    @staticmethod
    @transaction.atomic
    def update_product(*, product: Product, data: dict) -> Product:
        for field, value in data.items():
            setattr(product, field, value)

        product.save()
        return product

    @staticmethod
    @transaction.atomic
    def set_primary_image(*, image: ProductImage) -> ProductImage:
        ProductImage.objects.filter(
            product=image.product,
            is_primary=True,
        ).exclude(pk=image.pk).update(is_primary=False)

        image.is_primary = True
        image.save(update_fields=["is_primary"])
        return image

    @staticmethod
    @transaction.atomic
    def decrease_stock(
            *,
            product_id: int,
            quantity: int,
            variant_id: int | None = None,
    ) -> Product | ProductVariant:
        if quantity <= 0:
            raise ValidationError("تعداد باید بیشتر از صفر باشد.")

        if variant_id:
            item = get_object_or_404(
                ProductVariant.objects.select_for_update(),
                pk=variant_id,
                product_id=product_id,
                is_active=True,
            )

            if item.stock < quantity:
                raise InsufficientStockError("موجودی این تنوع محصول کافی نیست.")

            item.stock -= quantity
            item.save(update_fields=["stock"])
            return item

        product = get_object_or_404(
            Product.objects.select_for_update(),
            pk=product_id,
            is_available=True,
        )

        if product.stock < quantity:
            raise InsufficientStockError("موجودی محصول کافی نیست.")

        product.stock -= quantity
        product.save(update_fields=["stock"])
        return product

    @staticmethod
    @transaction.atomic
    def increase_stock(
            *,
            product_id: int,
            quantity: int,
            variant_id: int | None = None,
    ) -> Product | ProductVariant:
        if quantity <= 0:
            raise ValidationError("تعداد باید بیشتر از صفر باشد.")

        if variant_id:
            item = get_object_or_404(
                ProductVariant.objects.select_for_update(),
                pk=variant_id,
                product_id=product_id,
            )
            item.stock += quantity
            item.save(update_fields=["stock"])
            return item

        product = get_object_or_404(
            Product.objects.select_for_update(),
            pk=product_id,
        )
        product.stock += quantity
        product.save(update_fields=["stock"])
        return product

from django.db import transaction
from django.shortcuts import get_object_or_404

from core.exceptions import InsufficientStockError, ValidationError

from .models import Product, ProductImage, ProductVariant


class ProductService:
    """
    عملیات تغییردهنده مربوط به محصول و موجودی.

    منطق سفارش در OrderService باقی می‌ماند.
    """

    @staticmethod
    @transaction.atomic
    def create_product(
            *,
            data: dict,
    ) -> Product:
        product = Product(
            **data,
        )

        product.full_clean()
        product.save()

        return product

    @staticmethod
    @transaction.atomic
    def update_product(
            *,
            product: Product,
            data: dict,
    ) -> Product:
        for field, value in data.items():
            setattr(
                product,
                field,
                value,
            )

        product.full_clean()
        product.save()

        return product

    @staticmethod
    @transaction.atomic
    def set_primary_image(
            *,
            image: ProductImage,
    ) -> ProductImage:
        ProductImage.objects.filter(
            product=image.product,
            is_primary=True,
        ).exclude(
            pk=image.pk,
        ).update(
            is_primary=False,
        )

        image.is_primary = True

        if not image.alt_text:
            image.alt_text = image.product.name

        image.save()

        return image

    @staticmethod
    @transaction.atomic
    def decrease_stock(
            *,
            product_id: int,
            quantity: int,
            variant_id: int | None = None,
    ):
        if quantity < 1:
            raise ValidationError(
                "تعداد باید بیشتر از صفر باشد."
            )

        if variant_id is not None:
            variant = get_object_or_404(
                ProductVariant.objects.select_for_update(),
                pk=variant_id,
                product_id=product_id,
                is_active=True,
            )

            if variant.stock < quantity:
                raise InsufficientStockError(
                    "موجودی این تنوع محصول کافی نیست."
                )

            variant.stock -= quantity

            variant.save(
                update_fields=[
                    "stock",
                ],
            )

            return variant

        product = get_object_or_404(
            Product.objects.select_for_update(),
            pk=product_id,
            is_available=True,
        )

        if product.stock < quantity:
            raise InsufficientStockError(
                "موجودی محصول کافی نیست."
            )

        product.stock -= quantity

        product.save(
            update_fields=[
                "stock",
            ],
        )

        return product

    @staticmethod
    @transaction.atomic
    def increase_stock(
            *,
            product_id: int,
            quantity: int,
            variant_id: int | None = None,
    ):
        if quantity < 1:
            raise ValidationError(
                "تعداد باید بیشتر از صفر باشد."
            )

        if variant_id is not None:
            variant = get_object_or_404(
                ProductVariant.objects.select_for_update(),
                pk=variant_id,
                product_id=product_id,
            )

            variant.stock += quantity

            variant.save(
                update_fields=[
                    "stock",
                ],
            )

            return variant

        product = get_object_or_404(
            Product.objects.select_for_update(),
            pk=product_id,
        )

        product.stock += quantity

        product.save(
            update_fields=[
                "stock",
            ],
        )

        return product

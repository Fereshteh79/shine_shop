from decimal import Decimal

from django.test import TestCase

from .models import Brand, Category, Product


class ProductTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="دسته تست",
            slug="test-category",
            is_active=True,
        )

        self.brand = Brand.objects.create(
            name="برند تست",
            slug="test-brand",
            is_active=True,
        )

        self.product = Product.objects.create(
            category=self.category,
            brand=self.brand,
            name="محصول تست",
            slug="test-product",
            sku="TEST-001",
            price=Decimal("100000"),
            stock=10,
            is_available=True,
        )

    def test_final_price_without_discount(self):
        self.assertEqual(
            self.product.final_price,
            Decimal("100000"),
        )

    def test_product_is_in_stock(self):
        self.assertTrue(self.product.in_stock)

    def test_discount_price(self):
        self.product.discount_price = Decimal("80000")
        self.product.save()

        self.product.refresh_from_db()

        self.assertEqual(
            self.product.final_price,
            Decimal("80000"),
        )

    def test_discount_percentage(self):
        self.product.discount_price = Decimal("80000")
        self.product.save()

        self.product.refresh_from_db()

        self.assertEqual(
            self.product.discount_percentage,
            20,
        )

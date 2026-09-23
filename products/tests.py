from decimal import Decimal

from django.test import TestCase

from .models import (
    Brand,
    Category,
    Product,
    ProductAttribute,
    ProductImage,
    ProductVariant,
)


class ProductModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(
            name="دسته تست",
            slug="test-category",
        )

        cls.brand = Brand.objects.create(
            name="برند تست",
            slug="test-brand",
        )

        cls.product = Product.objects.create(
            category=cls.category,
            brand=cls.brand,
            name="محصول تست",
            slug="test-product",
            sku="TEST-001",
            price=Decimal("100000.00"),
            stock=10,
            is_available=True,
        )

    def test_final_price_without_discount(self):
        self.assertEqual(
            self.product.final_price,
            Decimal("100000.00"),
        )

    def test_final_price_with_discount(self):
        self.product.discount_price = Decimal(
            "80000.00",
        )
        self.product.save()

        self.product.refresh_from_db()

        self.assertEqual(
            self.product.final_price,
            Decimal("80000.00"),
        )

    def test_invalid_discount_is_removed(self):
        self.product.discount_price = Decimal(
            "100000.00",
        )

        self.product.save()

        self.product.refresh_from_db()

        self.assertIsNone(
            self.product.discount_price,
        )

    def test_discount_percentage(self):
        self.product.discount_price = Decimal(
            "80000.00",
        )
        self.product.save()

        self.product.refresh_from_db()

        self.assertEqual(
            self.product.discount_percentage,
            20,
        )

    def test_product_in_stock(self):
        self.assertTrue(
            self.product.in_stock,
        )

    def test_product_out_of_stock(self):
        self.product.stock = 0

        self.assertFalse(
            self.product.in_stock,
        )

    def test_product_absolute_url(self):
        self.assertEqual(
            self.product.get_absolute_url(),
            "/products/test-product/",
        )

    def test_category_absolute_url(self):
        self.assertEqual(
            self.category.get_absolute_url(),
            "/shop/category/test-category/",
        )


class ProductVariantTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        category = Category.objects.create(
            name="دسته",
            slug="category",
        )

        product = Product.objects.create(
            category=category,
            name="محصول",
            slug="product",
            sku="PRODUCT-001",
            price=Decimal("100000"),
            stock=10,
            is_available=True,
        )

        cls.product = product

    def test_variant_uses_own_price(self):
        variant = ProductVariant.objects.create(
            product=self.product,
            name="سایز بزرگ",
            sku="PRODUCT-001-L",
            price=Decimal("120000"),
            stock=5,
        )

        self.assertEqual(
            variant.final_price,
            Decimal("120000"),
        )

    def test_variant_falls_back_to_product_price(self):
        variant = ProductVariant.objects.create(
            product=self.product,
            name="سایز کوچک",
            sku="PRODUCT-001-S",
            price=None,
            stock=5,
        )

        self.assertEqual(
            variant.final_price,
            self.product.final_price,
        )

    def test_variant_in_stock(self):
        variant = ProductVariant.objects.create(
            product=self.product,
            name="سایز متوسط",
            sku="PRODUCT-001-M",
            stock=2,
        )

        self.assertTrue(
            variant.in_stock,
        )


class ProductImageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        category = Category.objects.create(
            name="دسته تصویر",
            slug="image-category",
        )

        cls.product = Product.objects.create(
            category=category,
            name="محصول تصویر",
            slug="image-product",
            sku="IMAGE-001",
            price=Decimal("100000"),
        )

    def test_only_one_primary_image(self):
        first = ProductImage.objects.create(
            product=self.product,
            image="products/test-1.jpg",
            is_primary=True,
        )

        second = ProductImage.objects.create(
            product=self.product,
            image="products/test-2.jpg",
            is_primary=True,
        )

        first.refresh_from_db()

        self.assertFalse(
            first.is_primary,
        )

        self.assertTrue(
            second.is_primary,
        )


class ProductAttributeTests(TestCase):
    def test_product_attribute(self):
        category = Category.objects.create(
            name="ویژگی",
            slug="attribute-category",
        )

        product = Product.objects.create(
            category=category,
            name="محصول ویژگی",
            slug="attribute-product",
            sku="ATTRIBUTE-001",
            price=Decimal("50000"),
        )

        attribute = ProductAttribute.objects.create(
            product=product,
            name="جنس",
            value="طلا",
        )

        self.assertEqual(
            str(attribute),
            "جنس: طلا",
        )

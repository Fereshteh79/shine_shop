from decimal import Decimal

from django.test import TestCase

from accounts.models import User
from products.models import Category, Product, ProductVariant

from .models import Cart
from .services import CartService


class CartTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="cartuser",
            email="cart@example.com",
            password="StrongPassword123!",
        )

        category = Category.objects.create(
            name="دسته تست سبد",
            slug="cart-test-category",
            is_active=True,
        )

        self.product = Product.objects.create(
            category=category,
            name="محصول سبد تست",
            slug="cart-test-product",
            sku="CART-001",
            price=Decimal("150000"),
            stock=10,
            is_available=True,
        )

    def test_create_cart(self):
        cart = CartService.get_or_create_cart(user=self.user)

        self.assertEqual(cart.user, self.user)
        self.assertEqual(Cart.objects.count(), 1)

    def test_add_item(self):
        item = CartService.add_item(
            user=self.user,
            product_id=self.product.id,
            quantity=2,
        )

        self.assertEqual(item.quantity, 2)
        self.assertEqual(item.line_total, Decimal("300000"))

    def test_add_same_item_merges(self):
        CartService.add_item(user=self.user, product_id=self.product.id, quantity=2)
        CartService.add_item(user=self.user, product_id=self.product.id, quantity=3)

        cart = Cart.objects.get(user=self.user)
        self.assertEqual(cart.items.count(), 1)
        self.assertEqual(cart.items.first().quantity, 5)

    def test_add_more_than_stock_raises(self):
        with self.assertRaises(Exception):
            CartService.add_item(
                user=self.user,
                product_id=self.product.id,
                quantity=11,
            )

    def test_update_item(self):
        item = CartService.add_item(
            user=self.user,
            product_id=self.product.id,
            quantity=2,
        )

        CartService.update_item(user=self.user, item_id=item.id, quantity=4)
        item.refresh_from_db()

        self.assertEqual(item.quantity, 4)

    def test_remove_item(self):
        item = CartService.add_item(
            user=self.user,
            product_id=self.product.id,
            quantity=1,
        )

        CartService.remove_item(user=self.user, item_id=item.id)

        self.assertFalse(self.user.cart.items.filter(pk=item.id).exists())

    def test_clear_cart(self):
        CartService.add_item(user=self.user, product_id=self.product.id, quantity=2)
        CartService.clear_cart(user=self.user)

        self.assertEqual(self.user.cart.items.count(), 0)

    def test_variant_stock_validation(self):
        variant = ProductVariant.objects.create(
            product=self.product,
            name="رنگ طلایی",
            sku="CART-001-G",
            stock=2,
            is_active=True,
        )

        with self.assertRaises(Exception):
            CartService.add_item(
                user=self.user,
                product_id=self.product.id,
                quantity=3,
                variant_id=variant.id,
            )

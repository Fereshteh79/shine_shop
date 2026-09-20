from django.test import TestCase

from products.models import Category, Product
from .models import Wishlist, WishlistItem
from .services import WishlistService


class WishlistTests(TestCase):

    def setUp(self):
        self.category = Category.objects.create(
            name="Test Category",
            slug="test-category",
        )

        self.product = Product.objects.create(
            category=self.category,
            name="Test Product",
            slug="test-product",
            sku="TEST-001",
            price=100000,
            stock=10,
            is_available=True,
        )

        self.user = self._create_user()

    def _create_user(self):
        from accounts.models import User

        return User.objects.create_user(
            username="wishlistuser",
            email="wishlist@example.com",
            password="StrongPassword123!",
        )

    def test_add_product_to_wishlist(self):
        item, created = WishlistService.add_product(
            user=self.user,
            product=self.product,
        )

        self.assertTrue(created)
        self.assertEqual(item.product, self.product)
        self.assertEqual(
            WishlistItem.objects.filter(
                wishlist__user=self.user,
                product=self.product,
            ).count(),
            1,
        )

    def test_remove_product_from_wishlist(self):
        WishlistService.add_product(
            user=self.user,
            product=self.product,
        )

        removed = WishlistService.remove_product(
            user=self.user,
            product=self.product,
        )

        self.assertTrue(removed)
        self.assertFalse(
            WishlistItem.objects.filter(
                wishlist__user=self.user,
                product=self.product,
            ).exists()
        )

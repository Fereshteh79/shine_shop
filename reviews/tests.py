from django.contrib.auth import get_user_model
from django.test import TestCase

from core.constants import OrderStatus
from core.exceptions import ValidationError
from orders.models import Order, OrderItem
from products.models import Category, Product

from .models import Review
from .services import ReviewService

User = get_user_model()


class ReviewServiceTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="review-user",
            email="review@example.com",
            password="StrongPassword123!",
        )

        self.category = Category.objects.create(
            name="Test Category",
            slug="test-category",
        )

        self.product = Product.objects.create(
            category=self.category,
            name="Test Product",
            slug="test-product",
            sku="TEST-001",
            price="100.00",
            stock=10,
            is_available=True,
        )

    def test_user_cannot_review_without_purchase(self):
        with self.assertRaises(ValidationError):
            ReviewService.create_review(
                user=self.user,
                product=self.product,
                rating=5,
                title="عالی",
                comment="محصول بسیار خوبی بود.",
            )

    def test_purchased_user_can_create_review(self):
        order = Order.objects.create(
            user=self.user,
            status=OrderStatus.PAID,
            subtotal="100.00",
            shipping_cost="0.00",
            discount_amount="0.00",
            total_amount="100.00",
            recipient_name="Test User",
            phone_number="09120000000",
            province="Tehran",
            city="Tehran",
            address="Test Address",
            postal_code="1234567890",
        )

        OrderItem.objects.create(
            order=order,
            product=self.product,
            product_name=self.product.name,
            sku=self.product.sku,
            quantity=1,
            unit_price="100.00",
            total_price="100.00",
        )

        review = ReviewService.create_review(
            user=self.user,
            product=self.product,
            rating=5,
            title="عالی",
            comment="محصول بسیار خوبی بود.",
        )

        self.assertEqual(review.user, self.user)
        self.assertEqual(review.product, self.product)
        self.assertFalse(review.is_approved)

    def test_user_cannot_create_duplicate_review(self):
        Review.objects.create(
            user=self.user,
            product=self.product,
            rating=5,
            title="عالی",
            comment="محصول بسیار خوبی بود.",
        )

        with self.assertRaises(ValidationError):
            ReviewService.create_review(
                user=self.user,
                product=self.product,
                rating=4,
                title="خوب",
                comment="این یک دیدگاه جدید است.",
            )

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from cart.models import Cart, CartItem
from core.constants import OrderStatus
from core.exceptions import InsufficientStockError, ValidationError
from products.models import Brand, Category, Product, ProductVariant

from .models import Order, OrderItem
from .services import OrderService


class OrderServiceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="orderuser",
            email="order@example.com",
            password="StrongPassword123!",
        )

        cls.category = Category.objects.create(
            name="زیورآلات",
            slug="jewelry",
        )

        cls.brand = Brand.objects.create(
            name="Shine",
            slug="shine",
        )

    def setUp(self):
        self.cart = Cart.objects.create(user=self.user)

    def create_product(
            self,
            *,
            name="گردنبند طلا",
            sku="SKU-001",
            price="1000000.00",
            stock=10,
    ):
        return Product.objects.create(
            category=self.category,
            brand=self.brand,
            name=name,
            slug=f"{sku.lower()}",
            sku=sku,
            price=Decimal(price),
            stock=stock,
            is_available=True,
        )

    def shipping_data(self):
        return {
            "recipient_name": "کاربر تست",
            "phone_number": "09120000000",
            "province": "تهران",
            "city": "تهران",
            "address": "خیابان تست، پلاک ۱",
            "postal_code": "1234567890",
            "notes": "توضیحات تست",
        }

    def add_cart_item(self, product, quantity=1, variant=None):
        return CartItem.objects.create(
            cart=self.cart,
            product=product,
            variant=variant,
            quantity=quantity,
        )

    def test_create_order_from_cart(self):
        product = self.create_product(
            price="1500000.00",
            stock=5,
        )
        self.add_cart_item(product, quantity=2)

        order = OrderService.create_from_cart(
            user=self.user,
            shipping_data=self.shipping_data(),
        )

        self.assertEqual(order.status, OrderStatus.PENDING)
        self.assertEqual(order.subtotal, Decimal("3000000.00"))
        self.assertEqual(order.total_amount, Decimal("3000000.00"))
        self.assertIsNotNone(order.payment_expires_at)

        product.refresh_from_db()
        self.assertEqual(product.stock, 3)

        self.assertEqual(order.items.count(), 1)

        item = order.items.get()
        self.assertEqual(item.product_name, product.name)
        self.assertEqual(item.sku, product.sku)
        self.assertEqual(item.quantity, 2)
        self.assertEqual(item.unit_price, Decimal("1500000.00"))
        self.assertEqual(item.total_price, Decimal("3000000.00"))

        self.assertEqual(self.cart.items.count(), 0)

    def test_create_order_uses_discounted_price(self):
        product = self.create_product(
            price="2000000.00",
            stock=5,
        )
        product.discount_price = Decimal("1750000.00")
        product.save(update_fields=["discount_price"])

        self.add_cart_item(product, quantity=2)

        order = OrderService.create_from_cart(
            user=self.user,
            shipping_data=self.shipping_data(),
        )

        self.assertEqual(order.subtotal, Decimal("3500000.00"))
        self.assertEqual(order.total_amount, Decimal("3500000.00"))

        item = order.items.get()
        self.assertEqual(item.unit_price, Decimal("1750000.00"))
        self.assertEqual(item.total_price, Decimal("3500000.00"))

    def test_create_order_with_variant(self):
        product = self.create_product(
            name="انگشتر",
            sku="RING-001",
            price="3000000.00",
            stock=10,
        )

        variant = ProductVariant.objects.create(
            product=product,
            name="سایز ۱۸",
            sku="RING-001-18",
            price=Decimal("3500000.00"),
            stock=4,
            is_active=True,
        )

        self.add_cart_item(
            product,
            quantity=2,
            variant=variant,
        )

        order = OrderService.create_from_cart(
            user=self.user,
            shipping_data=self.shipping_data(),
        )

        variant.refresh_from_db()
        product.refresh_from_db()

        self.assertEqual(variant.stock, 2)
        self.assertEqual(product.stock, 10)

        item = order.items.get()
        self.assertEqual(item.variant_id, variant.id)
        self.assertEqual(item.variant_name, variant.name)
        self.assertEqual(item.sku, variant.sku)
        self.assertEqual(item.unit_price, Decimal("3500000.00"))
        self.assertEqual(item.total_price, Decimal("7000000.00"))

        self.assertEqual(order.total_amount, Decimal("7000000.00"))

    def test_create_order_fails_for_empty_cart(self):
        with self.assertRaisesMessage(
                ValidationError,
                "سبد خرید خالی است.",
        ):
            OrderService.create_from_cart(
                user=self.user,
                shipping_data=self.shipping_data(),
            )

    def test_create_order_fails_when_stock_is_insufficient(self):
        product = self.create_product(stock=2)
        self.add_cart_item(product, quantity=3)

        with self.assertRaises(InsufficientStockError):
            OrderService.create_from_cart(
                user=self.user,
                shipping_data=self.shipping_data(),
            )

        self.assertFalse(Order.objects.exists())

        product.refresh_from_db()
        self.assertEqual(product.stock, 2)

        self.assertEqual(self.cart.items.count(), 1)

    def test_cancel_order_restores_product_stock(self):
        product = self.create_product(stock=5)
        self.add_cart_item(product, quantity=2)

        order = OrderService.create_from_cart(
            user=self.user,
            shipping_data=self.shipping_data(),
        )

        product.refresh_from_db()
        self.assertEqual(product.stock, 3)

        cancelled_order = OrderService.cancel_order(
            user=self.user,
            order_id=order.id,
        )

        product.refresh_from_db()
        cancelled_order.refresh_from_db()

        self.assertEqual(product.stock, 5)
        self.assertEqual(
            cancelled_order.status,
            OrderStatus.CANCELLED,
        )
        self.assertIsNone(
            cancelled_order.payment_expires_at,
        )

    def test_cancel_order_cannot_be_cancelled_twice(self):
        product = self.create_product(stock=5)
        self.add_cart_item(product, quantity=2)

        order = OrderService.create_from_cart(
            user=self.user,
            shipping_data=self.shipping_data(),
        )

        OrderService.cancel_order(
            user=self.user,
            order_id=order.id,
        )

        with self.assertRaisesMessage(
                ValidationError,
                "این سفارش در وضعیت فعلی قابل لغو نیست.",
        ):
            OrderService.cancel_order(
                user=self.user,
                order_id=order.id,
            )

        product.refresh_from_db()
        self.assertEqual(product.stock, 5)

    def test_expire_order_restores_stock(self):
        product = self.create_product(stock=5)
        self.add_cart_item(product, quantity=2)

        order = OrderService.create_from_cart(
            user=self.user,
            shipping_data=self.shipping_data(),
        )

        product.refresh_from_db()
        self.assertEqual(product.stock, 3)

        order.payment_expires_at = timezone.now() - timedelta(minutes=1)
        order.save(update_fields=["payment_expires_at"])

        result = OrderService.expire_order(order.id)

        self.assertTrue(result)

        product.refresh_from_db()
        order.refresh_from_db()

        self.assertEqual(product.stock, 5)
        self.assertEqual(order.status, OrderStatus.CANCELLED)
        self.assertIsNone(order.payment_expires_at)

    def test_expire_order_does_nothing_before_deadline(self):
        product = self.create_product(stock=5)
        self.add_cart_item(product, quantity=2)

        order = OrderService.create_from_cart(
            user=self.user,
            shipping_data=self.shipping_data(),
        )

        result = OrderService.expire_order(order.id)

        product.refresh_from_db()
        order.refresh_from_db()

        self.assertFalse(result)
        self.assertEqual(product.stock, 3)
        self.assertEqual(order.status, OrderStatus.PENDING)

    def test_expire_pending_orders(self):
        product = self.create_product(stock=10)
        self.add_cart_item(product, quantity=2)

        order = OrderService.create_from_cart(
            user=self.user,
            shipping_data=self.shipping_data(),
        )

        order.payment_expires_at = timezone.now() - timedelta(minutes=1)
        order.save(update_fields=["payment_expires_at"])

        expired_count = OrderService.expire_pending_orders()

        product.refresh_from_db()
        order.refresh_from_db()

        self.assertEqual(expired_count, 1)
        self.assertEqual(product.stock, 10)
        self.assertEqual(order.status, OrderStatus.CANCELLED)

    def test_expire_pending_orders_ignores_active_orders(self):
        product = self.create_product(stock=10)
        self.add_cart_item(product, quantity=2)

        order = OrderService.create_from_cart(
            user=self.user,
            shipping_data=self.shipping_data(),
        )

        expired_count = OrderService.expire_pending_orders()

        product.refresh_from_db()
        order.refresh_from_db()

        self.assertEqual(expired_count, 0)
        self.assertEqual(product.stock, 8)
        self.assertEqual(order.status, OrderStatus.PENDING)


class OrderModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="modeluser",
            email="model@example.com",
            password="StrongPassword123!",
        )

        self.order = Order.objects.create(
            user=self.user,
            status=OrderStatus.PENDING,
            subtotal=Decimal("1000000.00"),
            shipping_cost=Decimal("0.00"),
            discount_amount=Decimal("0.00"),
            total_amount=Decimal("1000000.00"),
            recipient_name="کاربر تست",
            phone_number="09120000000",
            province="تهران",
            city="تهران",
            address="آدرس تست",
            postal_code="1234567890",
            payment_expires_at=timezone.now() + timedelta(minutes=10),
        )

    def test_is_paid(self):
        for status in (
                OrderStatus.PAID,
                OrderStatus.PROCESSING,
                OrderStatus.SHIPPED,
                OrderStatus.DELIVERED,
        ):
            self.order.status = status
            self.assertTrue(self.order.is_paid)

    def test_pending_order_is_not_paid(self):
        self.assertFalse(self.order.is_paid)

    def test_is_payment_expired(self):
        self.order.payment_expires_at = (
                timezone.now() - timedelta(minutes=1)
        )

        self.assertTrue(self.order.is_payment_expired)

    def test_pending_order_is_not_expired_before_deadline(self):
        self.assertFalse(self.order.is_payment_expired)

    def test_cancelled_order_is_not_payment_expired(self):
        self.order.status = OrderStatus.CANCELLED
        self.order.payment_expires_at = (
                timezone.now() - timedelta(minutes=1)
        )

        self.assertFalse(self.order.is_payment_expired)

    def test_remaining_payment_seconds(self):
        self.order.payment_expires_at = (
                timezone.now() + timedelta(seconds=120)
        )

        self.assertGreaterEqual(
            self.order.remaining_payment_seconds,
            119,
        )
        self.assertLessEqual(
            self.order.remaining_payment_seconds,
            120,
        )

    def test_remaining_payment_seconds_is_zero_without_deadline(self):
        self.order.payment_expires_at = None

        self.assertEqual(
            self.order.remaining_payment_seconds,
            0,
        )

    def test_remaining_payment_seconds_never_becomes_negative(self):
        self.order.payment_expires_at = (
                timezone.now() - timedelta(seconds=30)
        )

        self.assertEqual(
            self.order.remaining_payment_seconds,
            0,
        )

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.http import HttpRequest, Http404
from django.shortcuts import redirect, render
from django.views import View

from cart.models import Cart
from core.exceptions import InsufficientStockError, ValidationError

from .forms import CheckoutForm
from .models import Order
from .selectors import get_user_order, get_user_orders
from .services import OrderService

TRACK_MAX_ATTEMPTS = 10
TRACK_WINDOW_SECONDS = 300


class OrderListView(LoginRequiredMixin, View):
    template_name = "orders/order_list.html"

    def get(self, request: HttpRequest):
        return render(
            request,
            self.template_name,
            {"orders": get_user_orders(request.user)},
        )


class OrderDetailView(LoginRequiredMixin, View):
    template_name = "orders/order_detail.html"

    def get(self, request: HttpRequest, order_id: int):
        order = get_user_order(request.user, order_id)

        if order is None:
            raise Http404("سفارش مورد نظر یافت نشد.")

        # ⬇️ رفع حلقه بی‌نهایت تایمر: انقضای زنده سفارش منقضی‌شده
        if (
                order.status == "pending"
                and order.is_payment_expired
        ):
            OrderService.expire_order(order.pk)
            order.refresh_from_db()
            messages.info(
                request,
                "مهلت پرداخت این سفارش به پایان رسیده و لغو شد.",
            )

        return render(
            request,
            self.template_name,
            {"order": order},
        )


class CheckoutView(LoginRequiredMixin, View):
    template_name = "orders/checkout.html"

    def _get_cart(self, user):
        return (
            Cart.objects
            .filter(user=user)
            .prefetch_related("items__product__images", "items__variant")
            .first()
        )

    def get(self, request: HttpRequest):
        cart = self._get_cart(request.user)

        if not cart or not cart.items.exists():
            messages.info(request, "سبد خرید شما خالی است.")
            return redirect("cart:detail")

        return render(
            request,
            self.template_name,
            {"form": CheckoutForm(), "cart": cart},
        )

    def post(self, request: HttpRequest):
        cart = self._get_cart(request.user)

        if not cart or not cart.items.exists():
            messages.error(request, "سبد خرید شما خالی است.")
            return redirect("cart:detail")

        form = CheckoutForm(request.POST)

        if not form.is_valid():
            return render(
                request,
                self.template_name,
                {"form": form, "cart": cart},
                status=400,
            )

        try:
            order = OrderService.create_from_cart(
                user=request.user,
                shipping_data=form.cleaned_data,
            )

        except (InsufficientStockError, ValidationError) as exc:
            messages.error(request, str(exc))
            return render(
                request,
                self.template_name,
                {"form": form, "cart": cart},
                status=400,
            )

        messages.success(request, f"سفارش #{order.id} ایجاد شد.")
        return redirect("payments:start", order_id=order.id)


class CancelOrderView(LoginRequiredMixin, View):

    def post(self, request: HttpRequest, order_id: int):
        try:
            OrderService.cancel_order(user=request.user, order_id=order_id)

        except ValidationError as exc:
            messages.error(request, str(exc))

        else:
            messages.success(request, "سفارش با موفقیت لغو شد.")

        return redirect("orders:detail", order_id=order_id)


class TrackOrderView(View):
    """
    پیگیری عمومی سفارش با کد رهگیری — بدون نیاز به ورود.
    با throttle ساده روی IP محافظت می‌شود.
    """

    template_name = "shop/track_order.html"

    def get(self, request: HttpRequest):
        return render(request, self.template_name, {})

    def post(self, request: HttpRequest):
        ip = request.META.get("REMOTE_ADDR", "")
        cache_key = f"track_attempts_{ip}"

        attempts = cache.get(cache_key, 0)

        if attempts >= TRACK_MAX_ATTEMPTS:
            messages.error(
                request,
                "تعداد تلاش‌های شما زیاد است. چند دقیقه بعد دوباره امتحان کنید.",
            )
            return render(request, self.template_name, {}, status=429)

        cache.set(
            cache_key,
            attempts + 1,
            TRACK_WINDOW_SECONDS,
        )

        code = request.POST.get("tracking_code", "").strip()

        order = None

        if code:
            order = (
                Order.objects
                .filter(tracking_code=code)
                .prefetch_related("items")
                .first()
            )

        return render(
            request,
            self.template_name,
            {"order": order, "searched_code": code},
        )

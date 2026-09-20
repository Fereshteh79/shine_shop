from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest
from django.shortcuts import redirect, render
from django.views import View

from cart.models import Cart
from core.exceptions import InsufficientStockError, ValidationError

from .forms import CheckoutForm
from .selectors import get_user_order, get_user_orders
from .services import OrderService


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
        form = CheckoutForm(request.POST)

        if not form.is_valid():
            return render(
                request,
                self.template_name,
                {"form": form, "cart": self._get_cart(request.user)},
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
                {"form": form, "cart": self._get_cart(request.user)},
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

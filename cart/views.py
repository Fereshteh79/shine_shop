from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View

from core.exceptions import InsufficientStockError, ValidationError

from .forms import AddToCartForm, UpdateCartItemForm
from .selectors import get_user_cart
from .services import CartService


def _safe_redirect(request: HttpRequest, fallback: str = "cart:detail") -> HttpResponse:
    """بازگشت امن به صفحه قبلی — محافظت در برابر open-redirect."""
    referer = request.META.get("HTTP_REFERER", "")

    if referer and url_has_allowed_host_and_scheme(
            referer,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
    ):
        return redirect(referer)

    return redirect(fallback)


class CartDetailView(LoginRequiredMixin, View):
    template_name = "cart/cart_detail.html"

    def get(self, request: HttpRequest):
        return render(
            request,
            self.template_name,
            {"cart": get_user_cart(request.user)},
        )


class AddToCartView(LoginRequiredMixin, View):

    def post(self, request: HttpRequest, product_id: int):
        form = AddToCartForm(request.POST)

        if not form.is_valid():
            messages.error(request, "اطلاعات وارد شده برای سبد خرید معتبر نیست.")
            return _safe_redirect(request)

        try:
            CartService.add_item(
                user=request.user,
                product_id=product_id,
                quantity=form.cleaned_data["quantity"],
                variant_id=form.cleaned_data.get("variant"),
            )

        except (InsufficientStockError, ValidationError) as exc:
            messages.error(request, str(exc))
            return _safe_redirect(request)

        messages.success(request, "محصول به سبد خرید اضافه شد.")
        return redirect("cart:detail")


class UpdateCartItemView(LoginRequiredMixin, View):

    def post(self, request: HttpRequest, item_id: int):
        form = UpdateCartItemForm(request.POST)

        if not form.is_valid():
            messages.error(request, "تعداد وارد شده معتبر نیست.")
            return redirect("cart:detail")

        try:
            CartService.update_item(
                user=request.user,
                item_id=item_id,
                quantity=form.cleaned_data["quantity"],
            )

        except (InsufficientStockError, ValidationError) as exc:
            messages.error(request, str(exc))

        else:
            messages.success(request, "تعداد محصول بروزرسانی شد.")

        return redirect("cart:detail")


class RemoveCartItemView(LoginRequiredMixin, View):

    def post(self, request: HttpRequest, item_id: int):
        CartService.remove_item(user=request.user, item_id=item_id)
        messages.success(request, "محصول از سبد خرید حذف شد.")
        return redirect("cart:detail")


class ClearCartView(LoginRequiredMixin, View):

    def post(self, request: HttpRequest):
        CartService.clear_cart(user=request.user)
        messages.success(request, "سبد خرید خالی شد.")
        return redirect("cart:detail")

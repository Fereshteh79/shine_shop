from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from core.utils import safe_redirect
from products.models import Product

from .selectors import get_user_wishlist
from .services import WishlistService


class WishlistView(LoginRequiredMixin, View):
    template_name = "wishlist/wishlist.html"

    def get(self, request: HttpRequest):
        return render(
            request,
            self.template_name,
            {"wishlist": get_user_wishlist(request.user)},
        )


class WishlistToggleView(LoginRequiredMixin, View):

    def post(self, request: HttpRequest, product_id: int):
        product = get_object_or_404(Product, pk=product_id, is_available=True)

        added = WishlistService.toggle_product(user=request.user, product=product)

        messages.success(
            request,
            "محصول به علاقه‌مندی‌ها اضافه شد."
            if added
            else "محصول از علاقه‌مندی‌ها حذف شد.",
        )

        return safe_redirect(
            request,
            request.POST.get("next"),
            fallback="shop:home",
        )


class WishlistRemoveView(LoginRequiredMixin, View):

    def post(self, request: HttpRequest, product_id: int):
        product = get_object_or_404(Product, pk=product_id)

        WishlistService.remove_product(user=request.user, product=product)

        messages.success(request, "محصول از علاقه‌مندی‌ها حذف شد.")

        return safe_redirect(
            request,
            request.POST.get("next"),
            fallback="wishlist:list",
        )


class WishlistClearView(LoginRequiredMixin, View):

    def post(self, request: HttpRequest):
        WishlistService.clear(user=request.user)

        messages.success(request, "لیست علاقه‌مندی‌ها خالی شد.")

        return redirect("wishlist:list")

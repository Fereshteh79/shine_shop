from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from core.exceptions import ValidationError
from products.models import Product

from .forms import ReviewForm
from .models import Review
from .selectors import get_user_review
from .services import ReviewService


class ReviewCreateView(LoginRequiredMixin, View):
    template_name = "reviews/review_form.html"

    def _get_product(
            self,
            product_slug: str,
    ) -> Product:
        return get_object_or_404(
            Product,
            slug=product_slug,
            is_available=True,
        )

    def get(
            self,
            request: HttpRequest,
            product_slug: str,
    ):
        product = self._get_product(product_slug)

        if get_user_review(
                user=request.user,
                product=product,
        ):
            messages.info(
                request,
                "شما قبلاً برای این محصول دیدگاه ثبت کرده‌اید.",
            )
            return redirect(
                "products:detail",
                slug=product.slug,
            )

        return render(
            request,
            self.template_name,
            {
                "product": product,
                "form": ReviewForm(),
            },
        )

    def post(
            self,
            request: HttpRequest,
            product_slug: str,
    ):
        product = self._get_product(product_slug)
        form = ReviewForm(request.POST)

        if not form.is_valid():
            return render(
                request,
                self.template_name,
                {
                    "product": product,
                    "form": form,
                },
            )

        try:
            ReviewService.create_review(
                user=request.user,
                product=product,
                rating=form.cleaned_data["rating"],
                title=form.cleaned_data["title"],
                comment=form.cleaned_data["comment"],
            )
        except ValidationError as exc:
            messages.error(request, str(exc))
            return redirect(
                "products:detail",
                slug=product.slug,
            )

        messages.success(
            request,
            "دیدگاه شما ثبت شد و پس از بررسی نمایش داده خواهد شد.",
        )

        return redirect(
            "products:detail",
            slug=product.slug,
        )


class ReviewUpdateView(LoginRequiredMixin, View):
    template_name = "reviews/review_form.html"

    def _get_review(
            self,
            request: HttpRequest,
            review_id: int,
    ) -> Review:
        return get_object_or_404(
            Review,
            pk=review_id,
            user=request.user,
        )

    def get(
            self,
            request: HttpRequest,
            review_id: int,
    ):
        review = self._get_review(
            request,
            review_id,
        )

        return render(
            request,
            self.template_name,
            {
                "product": review.product,
                "review": review,
                "form": ReviewForm(instance=review),
            },
        )

    def post(
            self,
            request: HttpRequest,
            review_id: int,
    ):
        review = self._get_review(
            request,
            review_id,
        )
        form = ReviewForm(
            request.POST,
            instance=review,
        )

        if not form.is_valid():
            return render(
                request,
                self.template_name,
                {
                    "product": review.product,
                    "review": review,
                    "form": form,
                },
            )

        try:
            ReviewService.update_review(
                review=review,
                user=request.user,
                rating=form.cleaned_data["rating"],
                title=form.cleaned_data["title"],
                comment=form.cleaned_data["comment"],
            )
        except ValidationError as exc:
            messages.error(request, str(exc))
            return redirect(
                "products:detail",
                slug=review.product.slug,
            )

        messages.success(
            request,
            "دیدگاه شما ویرایش شد و دوباره برای بررسی ارسال شد.",
        )

        return redirect(
            "products:detail",
            slug=review.product.slug,
        )


class ReviewDeleteView(LoginRequiredMixin, View):

    def post(
            self,
            request: HttpRequest,
            review_id: int,
    ):
        review = get_object_or_404(
            Review,
            pk=review_id,
            user=request.user,
        )
        product_slug = review.product.slug

        try:
            ReviewService.delete_review(
                review=review,
                user=request.user,
            )
        except ValidationError as exc:
            messages.error(
                request,
                str(exc),
            )
        else:
            messages.success(
                request,
                "دیدگاه شما حذف شد.",
            )

        return redirect(
            "products:detail",
            slug=product_slug,
        )

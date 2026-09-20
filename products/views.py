from django.contrib import messages
from django.core.paginator import Paginator
from django.http import Http404, HttpRequest
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View

from cart.services import CartService
from core.exceptions import InsufficientStockError, ValidationError

from .filters import ProductFilter
from .forms import AddToCartForm
from .selectors import (
    get_available_products,
    get_product_detail,
    get_related_products,
    search_products,
)
from .services import ProductService

PAGE_SIZE = 12


def _paginate(request, queryset, page_size: int = PAGE_SIZE):
    paginator = Paginator(queryset, page_size)
    page = paginator.get_page(request.GET.get("page"))

    params = request.GET.copy()
    params.pop("page", None)

    return page, params.urlencode()


class ProductListView(View):
    template_name = "products/product_list.html"

    def get(self, request: HttpRequest):
        sort = request.GET.get("sort", "newest")
        products = get_available_products(sort=sort)

        filterset = ProductFilter(
            request.GET or None,
            queryset=products,
        )

        page, querystring = _paginate(request, filterset.qs)

        return render(
            request,
            self.template_name,
            {
                "products": page,
                "filter": filterset,
                "querystring": querystring,
                "selected_sort": sort,
            },
        )


class ProductSearchView(View):
    template_name = "products/search.html"

    def get(self, request: HttpRequest):
        query = request.GET.get("q", "").strip()
        products = search_products(query)
        page, querystring = _paginate(request, products)

        return render(
            request,
            self.template_name,
            {
                "products": page,
                "query": query,
                "querystring": querystring,
            },
        )


class ProductDetailView(View):
    template_name = "products/product_detail.html"

    def get(self, request: HttpRequest, slug: str):
        product = get_product_detail(slug)

        if product is None:
            raise Http404("محصول مورد نظر یافت نشد.")

        from reviews.selectors import (
            get_product_review_summary,
            get_product_reviews,
            get_user_review,
        )
        from reviews.services import ReviewService

        purchased = False

        if request.user.is_authenticated:
            purchased = ReviewService._user_purchased_product(
                user=request.user,
                product=product,
            )

        return render(
            request,
            self.template_name,
            {
                "product": product,
                "related_products": get_related_products(product=product),
                "add_to_cart_form": AddToCartForm(),
                "reviews": get_product_reviews(product),
                "review_summary": get_product_review_summary(product),
                "user_review": (
                    get_user_review(user=request.user, product=product)
                    if request.user.is_authenticated
                    else None
                ),
                "purchased": purchased,
            },
        )

    def post(self, request: HttpRequest, slug: str):
        product = get_product_detail(slug)

        if product is None:
            raise Http404("محصول مورد نظر یافت نشد.")

        if not request.user.is_authenticated:
            login_url = reverse("accounts:login")
            return redirect(f"{login_url}?next={request.path}")

        form = AddToCartForm(request.POST)

        if not form.is_valid():
            messages.error(request, "اطلاعات محصول معتبر نیست.")
            return redirect("products:detail", slug=product.slug)

        try:
            CartService.add_item(
                user=request.user,
                product_id=product.id,
                quantity=form.cleaned_data["quantity"],
                variant_id=form.cleaned_data["variant"],
            )

        except (InsufficientStockError, ValidationError) as exc:
            messages.error(request, str(exc))
            return redirect("products:detail", slug=product.slug)

        messages.success(request, "محصول با موفقیت به سبد خرید اضافه شد.")
        return redirect("cart:detail")


# API-style ویو برای DRF (اختیاری — بعداً برای اپلیکیشن موبایل)
from rest_framework import generics  # noqa: E402

from .models import Product  # noqa: E402


class ProductAPIListView(generics.ListAPIView):
    queryset = Product.objects.filter(is_available=True).select_related(
        "category", "brand",
    )
    filterset_fields = ("category__slug", "brand__slug")

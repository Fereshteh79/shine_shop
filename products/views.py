import json

from django.contrib import messages
from django.core.paginator import Paginator
from django.http import Http404, HttpRequest
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View

from cart.services import CartService
from core.exceptions import (
    InsufficientStockError,
    ValidationError,
)

from .filters import ProductFilter
from .forms import AddToCartForm
from .models import Category
from .selectors import (
    get_available_products,
    get_product_detail,
    get_related_products,
    search_products,
)

PAGE_SIZE = 12


def paginate_queryset(request: HttpRequest, queryset, *, page_size: int = PAGE_SIZE):
    paginator = Paginator(queryset, page_size)
    page = paginator.get_page(request.GET.get("page"))

    params = request.GET.copy()
    params.pop("page", None)

    return page, params.urlencode()


def build_product_schema(request: HttpRequest, product) -> dict:
    """اسکیمای Product + BreadcrumbList — به‌جای ساخت شکننده JSON در تمپلیت."""
    images = [
        request.build_absolute_uri(img.image.url)
        for img in product.images.all()
    ]

    schema = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": product.name,
        "description": product.seo_description,
        "sku": product.sku,
        "brand": {
            "@type": "Brand",
            "name": product.brand.name if product.brand else "Shine",
        },
        "offers": {
            "@type": "Offer",
            "priceCurrency": "IRT",
            "price": str(int(product.final_price)),
            "availability": (
                "https://schema.org/InStock"
                if product.in_stock
                else "https://schema.org/OutOfStock"
            ),
            "url": request.build_absolute_uri(product.get_absolute_url()),
        },
    }

    if images:
        schema["image"] = images

    breadcrumb = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": 1,
                "name": "خانه",
                "item": request.build_absolute_uri(reverse("shop:home")),
            },
            {
                "@type": "ListItem",
                "position": 2,
                "name": "فروشگاه",
                "item": request.build_absolute_uri(reverse("products:list")),
            },
        ],
    }

    if product.category:
        breadcrumb["itemListElement"].append({
            "@type": "ListItem",
            "position": 3,
            "name": product.category.name,
            "item": request.build_absolute_uri(product.category.get_absolute_url()),
        })

    return {"product": schema, "breadcrumb": breadcrumb}


def schema_script(data: dict) -> str:
    """خروجی امن برای تگ script — بدون نیاز به escape در تمپلیت."""
    dumped = json.dumps(data, ensure_ascii=False)
    # جلوگیری از تزریق </script>
    return dumped.replace("</", "<\\/")


class ProductListView(View):
    template_name = "products/product_list.html"

    def get(self, request: HttpRequest):
        sort = request.GET.get("sort", "newest").strip()

        products = get_available_products(sort=sort)
        product_filter = ProductFilter(request.GET or None, queryset=products)

        page, querystring = paginate_queryset(request, product_filter.qs)

        return render(request, self.template_name, {
            "products": page,
            "filter": product_filter,
            "querystring": querystring,
            "selected_sort": sort,
            "categories": Category.objects.filter(is_active=True),
            "page_elided": products.paginator.get_elided_page_range(products.number, on_each_side=2, on_ends=1),
        })


class ProductSearchView(View):
    template_name = "products/search.html"

    def get(self, request: HttpRequest):
        query = request.GET.get("q", "").strip()
        products = search_products(query)
        page, querystring = paginate_queryset(request, products)

        return render(request, self.template_name, {
            "products": page,
            "query": query,
            "querystring": querystring,
        })


class ProductDetailView(View):
    template_name = "products/product_detail.html"

    def get_product(self, slug: str):
        product = get_product_detail(slug)
        if product is None:
            raise Http404("محصول مورد نظر یافت نشد.")
        return product

    def get(self, request: HttpRequest, slug: str):
        product = self.get_product(slug)

        from reviews.selectors import (
            get_product_review_summary,
            get_product_reviews,
            get_user_review,
        )
        from reviews.services import ReviewService

        purchased = False
        if request.user.is_authenticated:
            purchased = ReviewService._user_purchased_product(
                user=request.user, product=product,
            )

        schema = build_product_schema(request, product)

        context = {
            "product": product,
            "related_products": get_related_products(product=product),
            "add_to_cart_form": AddToCartForm(),
            "reviews": get_product_reviews(product),
            "review_summary": get_product_review_summary(product),
            "user_review": (
                get_user_review(user=request.user, product=product)
                if request.user.is_authenticated else None
            ),
            "purchased": purchased,
            "product_schema_json": schema_script(schema["product"]),
            "breadcrumb_schema_json": schema_script(schema["breadcrumb"]),
        }

        return render(request, self.template_name, context)

    def post(self, request: HttpRequest, slug: str):
        product = self.get_product(slug)

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
                product_id=product.pk,
                quantity=form.cleaned_data["quantity"],
                variant_id=form.cleaned_data["variant"],
            )
        except (InsufficientStockError, ValidationError) as exc:
            messages.error(request, str(exc))
            return redirect("products:detail", slug=product.slug)

        messages.success(request, "محصول با موفقیت به سبد خرید اضافه شد.")
        return redirect("cart:detail")

from django.core.paginator import Paginator
from django.db.models import QuerySet
from django.http import Http404, HttpRequest
from django.shortcuts import render
from django.views import View

from products.models import Product

from .selectors import (
    get_active_brands,
    get_active_categories,
    get_category,
    get_home_products,
)
from .services import ShopService

PRODUCTS_PER_PAGE = 12


class PaginatedListView(View):
    """نمای پایه برای لیست‌های صفحه‌بندی‌شده با حفظ پارامترهای کوئری."""

    template_name: str = ""
    page_size: int = PRODUCTS_PER_PAGE

    def get_paginated_context(
            self,
            request: HttpRequest,
            queryset: QuerySet[Product],
    ) -> dict:
        paginator = Paginator(queryset, self.page_size)
        page = paginator.get_page(request.GET.get("page"))

        # حفظ فیلترها در لینک‌های صفحه‌بندی
        params = request.GET.copy()
        params.pop("page", None)

        return {
            "products": page,
            "querystring": params.urlencode(),
        }


class HomeView(View):
    template_name = "shop/home.html"

    def get(self, request: HttpRequest):
        return render(
            request,
            self.template_name,
            {
                "featured_products": get_home_products(),
                "categories": get_active_categories(),
            },
        )


class ProductListView(PaginatedListView):
    template_name = "shop/product_list.html"

    def get(self, request: HttpRequest):
        query = request.GET.get("q", "").strip()
        category = request.GET.get("category", "").strip()
        brand = request.GET.get("brand", "").strip()
        sort = request.GET.get("sort", "newest").strip()

        products = ShopService.filter_products(
            query=query,
            category_slug=category,
            brand_slug=brand,
            sort=sort,
        )

        context = {
            "categories": get_active_categories(),
            "brands": get_active_brands(),
            "query": query,
            "selected_category": category,
            "selected_brand": brand,
            "selected_sort": sort,
            **self.get_paginated_context(request, products),
        }

        return render(request, self.template_name, context)


class CategoryView(PaginatedListView):
    template_name = "shop/product_list.html"

    def get(self, request: HttpRequest, slug: str):
        category = get_category(slug)

        if category is None:
            raise Http404("دسته‌بندی مورد نظر یافت نشد.")

        products = ShopService.filter_products(
            category_slug=category.slug,
            sort=request.GET.get("sort", "newest"),
        )

        context = {
            "category": category,
            "categories": get_active_categories(),
            "brands": get_active_brands(),
            "selected_category": category.slug,
            "selected_sort": request.GET.get("sort", "newest"),
            **self.get_paginated_context(request, products),
        }

        return render(request, self.template_name, context)


class SearchView(ProductListView):
    """جستجو — همان منطق لیست محصولات با query در آدرس."""
    pass

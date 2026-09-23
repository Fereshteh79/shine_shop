import django_filters
from django.db.models import Case, DecimalField, F, When

from .models import Product


class ProductFilter(django_filters.FilterSet):
    """
    Filters and sorting for Product queryset.

    Supported filters:
        - category
        - brand
        - min_price
        - max_price
        - sort

    The final product price is:
        discount_price if available
        otherwise price
    """

    category = django_filters.CharFilter(
        field_name="category__slug",
        label="دسته‌بندی",
    )

    brand = django_filters.CharFilter(
        field_name="brand__slug",
        label="برند",
    )

    min_price = django_filters.NumberFilter(
        method="filter_min_price",
        label="حداقل قیمت",
    )

    max_price = django_filters.NumberFilter(
        method="filter_max_price",
        label="حداکثر قیمت",
    )

    sort = django_filters.ChoiceFilter(
        choices=(
            ("newest", "جدیدترین"),
            ("oldest", "قدیمی‌ترین"),
            ("price_low", "ارزان‌ترین"),
            ("price_high", "گران‌ترین"),
            ("name", "الفبایی"),
        ),
        method="filter_sort",
        label="مرتب‌سازی",
    )

    class Meta:
        model = Product
        fields = (
            "category",
            "brand",
            "min_price",
            "max_price",
            "sort",
        )

    @staticmethod
    def _final_price_expression():
        """
        Returns the database expression for the product's final price.

        If a discount price exists, it is used.
        Otherwise, the regular price is used.
        """
        return Case(
            When(
                discount_price__isnull=False,
                then=F("discount_price"),
            ),
            default=F("price"),
            output_field=DecimalField(
                max_digits=12,
                decimal_places=2,
            ),
        )

    def _with_final_price(self, queryset):
        """
        Annotate queryset with the calculated final price.
        """
        return queryset.annotate(
            final_price=self._final_price_expression(),
        )

    def filter_min_price(self, queryset, name, value):
        """
        Filter products whose final price is greater than
        or equal to the given minimum price.
        """
        queryset = self._with_final_price(queryset)

        return queryset.filter(
            final_price__gte=value,
        )

    def filter_max_price(self, queryset, name, value):
        """
        Filter products whose final price is less than
        or equal to the given maximum price.
        """
        queryset = self._with_final_price(queryset)

        return queryset.filter(
            final_price__lte=value,
        )

    def filter_sort(self, queryset, name, value):
        """
        Sort products based on the requested option.
        """
        if value == "newest":
            return queryset.order_by("-created_at")

        if value == "oldest":
            return queryset.order_by("created_at")

        if value == "name":
            return queryset.order_by("name")

        if value in {"price_low", "price_high"}:
            queryset = self._with_final_price(queryset)

            ordering = (
                "final_price"
                if value == "price_low"
                else "-final_price"
            )

            return queryset.order_by(ordering)

        return queryset.order_by("-created_at")

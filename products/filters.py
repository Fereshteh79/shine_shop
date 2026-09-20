import django_filters

from .models import Product


class ProductFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(
        field_name="price",
        lookup_expr="gte",
        label="از قیمت",
    )
    max_price = django_filters.NumberFilter(
        field_name="price",
        lookup_expr="lte",
        label="تا قیمت",
    )
    category = django_filters.CharFilter(
        field_name="category__slug",
    )
    brand = django_filters.CharFilter(
        field_name="brand__slug",
    )
    sort = django_filters.CharFilter(method="filter_sort")

    class Meta:
        model = Product
        fields = (
            "category",
            "brand",
            "min_price",
            "max_price",
        )

    def filter_sort(self, queryset, name, value):
        ordering = {
            "newest": "-created_at",
            "oldest": "created_at",
            "price_low": "price",
            "price_high": "-price",
            "name": "name",
        }
        return queryset.order_by(ordering.get(value, "-created_at"))
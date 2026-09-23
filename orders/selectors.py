from django.db.models import Count, Prefetch

from .models import Order


def get_user_orders(user):
    """
    لیست سفارش‌ها — تعداد اقلام با annotate
    تا تمپلیت کوئری اضافه نزند.
    """
    return (
        Order.objects
        .filter(user=user)
        .annotate(items_count=Count("items"))
        .order_by("-created_at")
    )


def get_user_order(user, order_id):
    return (
        Order.objects
        .filter(user=user, pk=order_id)
        .prefetch_related(
            Prefetch("items", queryset=Order.items.select_related("product", "variant").get_queryset()),
        )
        .first()
    )

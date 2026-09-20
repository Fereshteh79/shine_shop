from .models import Order


def get_user_orders(user):
    return (
        Order.objects
        .filter(user=user)
        .prefetch_related("items")
        .order_by("-created_at")
    )


def get_user_order(user, order_id):
    return (
        Order.objects
        .filter(user=user, pk=order_id)
        .prefetch_related(
            "items__product",
            "items__variant",
        )
        .first()
    )

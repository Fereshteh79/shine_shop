from django.db.models import Avg, Count

from .models import Review


def get_product_reviews(product):
    return (
        Review.objects
        .filter(
            product=product,
            is_approved=True,
        )
        .select_related("user")
        .order_by("-created_at")
    )


def get_product_review_summary(product):
    return Review.objects.filter(
        product=product,
        is_approved=True,
    ).aggregate(
        average_rating=Avg("rating"),
        review_count=Count("id"),
    )


def get_user_review(*, user, product):
    return (
        Review.objects
        .filter(
            user=user,
            product=product,
        )
        .first()
    )

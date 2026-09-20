from .models import Payment


def get_user_payments(user):
    return (
        Payment.objects
        .filter(user=user)
        .select_related("order")
        .order_by("-created_at")
    )


def get_user_payment(user, payment_id):
    return (
        Payment.objects
        .filter(
            pk=payment_id,
            user=user,
        )
        .select_related("order")
        .first()
    )

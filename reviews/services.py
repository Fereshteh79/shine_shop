from django.db import transaction

from core.constants import OrderStatus
from core.exceptions import ValidationError

from .models import Review


class ReviewService:

    @staticmethod
    def _user_purchased_product(*, user, product):
        from orders.models import OrderItem

        return (
            OrderItem.objects
            .filter(
                product=product,
                order__user=user,
                order__status__in={
                    OrderStatus.PAID,
                    OrderStatus.PROCESSING,
                    OrderStatus.SHIPPED,
                    OrderStatus.DELIVERED,
                },
            )
            .exists()
        )

    @staticmethod
    @transaction.atomic
    def create_review(
            *,
            user,
            product,
            rating,
            title,
            comment,
    ):
        if not ReviewService._user_purchased_product(
                user=user,
                product=product,
        ):
            raise ValidationError(
                "برای ثبت دیدگاه باید این محصول را خریداری کرده باشید."
            )

        if Review.objects.filter(
                user=user,
                product=product,
        ).exists():
            raise ValidationError(
                "شما قبلاً برای این محصول دیدگاه ثبت کرده‌اید."
            )

        return Review.objects.create(
            user=user,
            product=product,
            rating=rating,
            title=title,
            comment=comment,
            is_approved=False,
        )

    @staticmethod
    @transaction.atomic
    def update_review(
            *,
            review,
            user,
            rating,
            title,
            comment,
    ):
        if review.user_id != user.id:
            raise ValidationError(
                "شما اجازه ویرایش این دیدگاه را ندارید."
            )

        review.rating = rating
        review.title = title
        review.comment = comment

        # هر ویرایش دوباره نیازمند تأیید مدیر است.
        review.is_approved = False

        review.save(
            update_fields=[
                "rating",
                "title",
                "comment",
                "is_approved",
                "updated_at",
            ]
        )

        return review

    @staticmethod
    @transaction.atomic
    def delete_review(*, review, user):
        if review.user_id != user.id:
            raise ValidationError(
                "شما اجازه حذف این دیدگاه را ندارید."
            )

        review.delete()

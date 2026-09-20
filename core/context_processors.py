from django.db.models import Count, Sum

from cart.models import Cart
from wishlist.models import Wishlist


def site_info(request):
    context = {
        "cart_count": 0,
        "wishlist_count": 0,
    }

    if not request.user.is_authenticated:
        return context

    # مجموع تعداد کالاهای سبد — یک کوئری سبک
    cart_total = (
        Cart.objects
        .filter(user=request.user)
        .aggregate(total=Sum("items__quantity"))["total"]
    )

    # تعداد محصولات علاقه‌مندی — با Count (نه Sum که idها را جمع می‌زند!)
    wishlist_total = (
        Wishlist.objects
        .filter(user=request.user)
        .aggregate(total=Count("items__id"))["total"]
    )

    context["cart_count"] = cart_total or 0
    context["wishlist_count"] = wishlist_total or 0

    return context

from django.urls import path

from .views import (
    WishlistClearView,
    WishlistRemoveView,
    WishlistToggleView,
    WishlistView,
)

app_name = "wishlist"

urlpatterns = [
    path("", WishlistView.as_view(), name="list"),
    path(
        "toggle/<int:product_id>/",
        WishlistToggleView.as_view(),
        name="toggle",
    ),
    path(
        "remove/<int:product_id>/",
        WishlistRemoveView.as_view(),
        name="remove",
    ),
    path(
        "clear/",
        WishlistClearView.as_view(),
        name="clear",
    ),
]

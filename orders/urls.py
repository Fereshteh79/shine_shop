from django.urls import path

from .views import (
    CancelOrderView,
    CheckoutView,
    OrderDetailView,
    OrderListView,
)

app_name = "orders"

urlpatterns = [
    path("", OrderListView.as_view(), name="list"),
    path(
        "checkout/",
        CheckoutView.as_view(),
        name="checkout",
    ),
    path(
        "<int:order_id>/",
        OrderDetailView.as_view(),
        name="detail",
    ),
    path(
        "<int:order_id>/cancel/",
        CancelOrderView.as_view(),
        name="cancel",
    ),
]

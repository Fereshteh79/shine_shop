from django.urls import path

from .views import (
    PaymentCallbackView,
    PaymentListView,
    PaymentStartView,
)

app_name = "payments"

urlpatterns = [
    path(
        "",
        PaymentListView.as_view(),
        name="list",
    ),

    path(
        "start/<int:order_id>/",
        PaymentStartView.as_view(),
        name="start",
    ),

    path(
        "callback/",
        PaymentCallbackView.as_view(),
        name="callback",
    ),
]

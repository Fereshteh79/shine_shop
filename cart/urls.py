from django.urls import path

from .views import (
    AddToCartView,
    CartDetailView,
    ClearCartView,
    RemoveCartItemView,
    UpdateCartItemView,
)

app_name = "cart"

urlpatterns = [
    path("", CartDetailView.as_view(), name="detail"),
    path("add/<int:product_id>/", AddToCartView.as_view(), name="add"),
    path("item/<int:item_id>/update/", UpdateCartItemView.as_view(), name="update"),
    path("item/<int:item_id>/remove/", RemoveCartItemView.as_view(), name="remove"),
    path("clear/", ClearCartView.as_view(), name="clear"),
]

from django.urls import path

from .views import (
    ReviewCreateView,
    ReviewDeleteView,
    ReviewUpdateView,
)

app_name = "reviews"

urlpatterns = [
    path(
        "product/<slug:product_slug>/create/",
        ReviewCreateView.as_view(),
        name="create",
    ),
    path(
        "<int:review_id>/edit/",
        ReviewUpdateView.as_view(),
        name="update",
    ),
    path(
        "<int:review_id>/delete/",
        ReviewDeleteView.as_view(),
        name="delete",
    ),
]

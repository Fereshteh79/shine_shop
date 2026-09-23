from django.urls import path

from .api import (
    ProductAPIDetailView,
    ProductAPIListView,
)
from .views import (
    ProductDetailView,
    ProductListView,
    ProductSearchView,
)

app_name = "products"

urlpatterns = [
    path(
        "",
        ProductListView.as_view(),
        name="list",
    ),
    path(
        "search/",
        ProductSearchView.as_view(),
        name="search",
    ),
    path(
        "api/",
        ProductAPIListView.as_view(),
        name="api-list",
    ),
    path(
        "api/<slug:slug>/",
        ProductAPIDetailView.as_view(),
        name="api-detail",
    ),
    path(
        "<slug:slug>/",
        ProductDetailView.as_view(),
        name="detail",
    ),
]

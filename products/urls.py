from django.urls import path

from .views import (
    ProductAPIListView,
    ProductDetailView,
    ProductListView,
    ProductSearchView,
)

app_name = "products"

urlpatterns = [
    path("", ProductListView.as_view(), name="list"),
    path("search/", ProductSearchView.as_view(), name="search"),
    path("api/", ProductAPIListView.as_view(), name="api-list"),
    path("<slug:slug>/", ProductDetailView.as_view(), name="detail"),
]

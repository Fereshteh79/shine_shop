from django.urls import path

from .views import CategoryView, HomeView, ProductListView, SearchView

app_name = "shop"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("shop/", ProductListView.as_view(), name="products"),
    path("shop/category/<slug:slug>/", CategoryView.as_view(), name="category"),
    path("search/", SearchView.as_view(), name="search"),
]

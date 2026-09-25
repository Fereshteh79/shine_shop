# accounts/urls.py

from django.urls import path

from .views import (
    OtpRequestView,
    OtpVerifyView,
    RegisterView,
    UserLoginView,
    UserLogoutView,
)

app_name = "accounts"

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", UserLoginView.as_view(), name="login"),
    path("logout/", UserLogoutView.as_view(), name="logout"),
    path("login/otp/", OtpRequestView.as_view(), name="otp_request"),
    path("login/otp/verify/", OtpVerifyView.as_view(), name="otp_verify"),
]

"""Viewهای احراز هویت و حساب کاربری اپ accounts.

جریان‌ها:
    1. ثبت‌نام با موبایل + رمز عبور  → ورود خودکار
    2. ورود با موبایل/ایمیل + رمز    → Django LoginView
    3. ورود با کد یکبارمصرف (OTP)    → دو مرحله: request + verify
    4. پروفایل: ویرایش اطلاعات + تغییر رمز عبور
"""

from __future__ import annotations

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import (
    forms as auth_forms,
    get_user_model,
    login,
    update_session_auth_hash,
)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views import View

from core.utils import get_client_ip, get_safe_next_url

from .forms import (
    LoginForm,
    OtpRequestForm,
    OtpVerifyForm,
    ProfileForm,
    RegisterForm,
)
from .models import Profile
from .services import (
    OTPError,
    OTP_PURPOSE_LOGIN,
    create_user,
    get_or_create_phone_user,
    request_otp,
    verify_otp,
)

User = get_user_model()

# --------------------------------------------------------------------------- #
# ثابت‌های session جریان OTP
# --------------------------------------------------------------------------- #

OTP_SESSION_KEY = getattr(settings, "OTP_SESSION_KEY", "accounts_otp_phone")
OTP_NEXT_SESSION_KEY = "accounts_otp_next"
OTP_SESSION_TTL = 600  # ثانیه — برابر با حداکثر زمان مجاز بین درخواست و تأیید کد

LOGIN_BACKEND = "accounts.backends.PhoneOrEmailBackend"


# --------------------------------------------------------------------------- #
# توابع کمکی خصوصی
# --------------------------------------------------------------------------- #


def _get_client_ip(request: HttpRequest) -> str | None:
    """IP واقعی کاربر با احتساب TRUSTED_PROXY_COUNT (پشت nginx هم درست کار می‌کند)."""
    return get_client_ip(request) or None


def _login_user(request: HttpRequest, user: User) -> None:
    """ورود صریح کاربر با backend پروژه."""
    login(request, user, backend=LOGIN_BACKEND)


def _clear_otp_session(request: HttpRequest) -> None:
    """پاک‌سازی کامل session جریان OTP و بازگرداندن expiry به حالت پیش‌فرض."""
    request.session.pop(OTP_SESSION_KEY, None)
    request.session.pop(OTP_NEXT_SESSION_KEY, None)
    request.session.set_expiry(None)


def _store_otp_session(request: HttpRequest, phone: str) -> None:
    """ذخیرهٔ شماره موبایل و آدرس بازگشت امن در session."""
    request.session[OTP_SESSION_KEY] = phone
    request.session[OTP_NEXT_SESSION_KEY] = get_safe_next_url(request, default="")
    request.session.set_expiry(OTP_SESSION_TTL)


# --------------------------------------------------------------------------- #
# ثبت‌نام
# --------------------------------------------------------------------------- #


class RegisterView(View):
    """ثبت‌نام با موبایل و رمز عبور + ورود خودکار پس از ثبت‌نام."""

    template_name = "accounts/register.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        if request.user.is_authenticated:
            return redirect("shop:home")

        return render(request, self.template_name, {"form": RegisterForm()})

    def post(self, request: HttpRequest) -> HttpResponse:
        if request.user.is_authenticated:
            return redirect("shop:home")

        form = RegisterForm(request.POST)

        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        user = create_user(
            phone_number=form.cleaned_data["phone_number"],
            password=form.cleaned_data["password1"],
            first_name=form.cleaned_data.get("first_name", ""),
            last_name=form.cleaned_data.get("last_name", ""),
            email=form.cleaned_data.get("email"),
        )

        _login_user(request, user)

        messages.success(
            request,
            f"{user.display_name} عزیز! حساب شما با موفقیت ساخته شد.",
        )

        return redirect(get_safe_next_url(request, default="") or "shop:home")


# --------------------------------------------------------------------------- #
# ورود با رمز عبور
# --------------------------------------------------------------------------- #


class UserLoginView(LoginView):
    """ورود با شماره موبایل یا ایمیل + رمز عبور."""

    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def form_valid(self, form: LoginForm) -> HttpResponse:
        messages.success(
            self.request,
            f"{form.get_user().display_name} عزیز، خوش برگشتی!",
        )

        return super().form_valid(form)


class UserLogoutView(LogoutView):
    """خروج از حساب (فقط POST)."""

    next_page = "shop:home"

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if request.user.is_authenticated:
            messages.info(request, "با موفقیت از حساب خود خارج شدید.")

        return super().dispatch(request, *args, **kwargs)


# --------------------------------------------------------------------------- #
# ورود با کد یکبارمصرف (دو مرحله)
# --------------------------------------------------------------------------- #


class OtpRequestView(View):
    """مرحلهٔ اول: دریافت شماره موبایل و ارسال کد."""

    template_name = "accounts/otp_request.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        if request.user.is_authenticated:
            return redirect("shop:home")

        return render(request, self.template_name, {"form": OtpRequestForm()})

    def post(self, request: HttpRequest) -> HttpResponse:
        if request.user.is_authenticated:
            return redirect("shop:home")

        form = OtpRequestForm(request.POST)

        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        phone = form.cleaned_data["phone_number"]

        try:
            request_otp(
                phone_number=phone,
                purpose=OTP_PURPOSE_LOGIN,
                ip_address=_get_client_ip(request),
            )
        except OTPError as exc:
            form.add_error("phone_number", str(exc))
            return render(request, self.template_name, {"form": form})

        _store_otp_session(request, phone)

        messages.success(request, "کد تأیید به شمارهٔ شما پیامک شد.")

        return redirect("accounts:otp_verify")


class OtpVerifyView(View):
    """مرحلهٔ دوم: تأیید کد و ورود/ساخت خودکار کاربر."""

    template_name = "accounts/otp_verify.html"

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if request.user.is_authenticated:
            return redirect("shop:home")

        if not request.session.get(OTP_SESSION_KEY):
            messages.warning(request, "ابتدا شمارهٔ موبایل خود را وارد کنید.")
            return redirect("accounts:otp_request")

        return super().dispatch(request, *args, **kwargs)

    def get(self, request: HttpRequest) -> HttpResponse:
        phone = request.session.get(OTP_SESSION_KEY, "")

        return render(
            request,
            self.template_name,
            {"phone": phone, "form": OtpVerifyForm()},
        )

    def post(self, request: HttpRequest) -> HttpResponse:
        phone = request.session.get(OTP_SESSION_KEY, "")

        if not phone:
            messages.warning(request, "ابتدا شمارهٔ موبایل خود را وارد کنید.")
            return redirect("accounts:otp_request")

        form = OtpVerifyForm(request.POST)

        if not form.is_valid():
            return render(
                request,
                self.template_name,
                {"phone": phone, "form": form},
            )

        try:
            verify_otp(
                phone_number=phone,
                code=form.cleaned_data["code"],
                purpose=OTP_PURPOSE_LOGIN,
            )
        except OTPError as exc:
            form.add_error("code", str(exc))
            return render(
                request,
                self.template_name,
                {"phone": phone, "form": form},
            )

        user = get_or_create_phone_user(phone)

        if not user.is_active:
            _clear_otp_session(request)
            messages.error(request, "حساب شما غیرفعال است.")
            return redirect("accounts:otp_request")

        _login_user(request, user)
        _clear_otp_session(request)

        messages.success(request, f"{user.display_name} عزیز، خوش آمدید!")

        # بازگشت به صفحه‌ای که کاربر از آن به ورود آمده بود (در صورت وجود).
        next_url = request.session.get(OTP_NEXT_SESSION_KEY, "")

        return redirect(next_url or "shop:home")


# --------------------------------------------------------------------------- #
# پروفایل
# --------------------------------------------------------------------------- #


@login_required
def profile_view(request: HttpRequest) -> HttpResponse:
    """نمایش و ویرایش پروفایل + تغییر رمز عبور (دو فرم مستقل در یک صفحه)."""

    profile, _ = Profile.objects.get_or_create(user=request.user)

    password_form = auth_forms.PasswordChangeForm(user=request.user)
    profile_form = ProfileForm(instance=profile)

    if request.method == "POST":

        if "update_profile" in request.POST:
            profile_form = ProfileForm(request.POST, request.FILES, instance=profile)

            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "اطلاعات پروفایل ذخیره شد.")
                return redirect("accounts:profile")

        elif "change_password" in request.POST:
            password_form = auth_forms.PasswordChangeForm(
                user=request.user,
                data=request.POST,
            )

            if password_form.is_valid():
                password_form.save()
                update_session_auth_hash(request, password_form.user)
                messages.success(request, "رمز عبور تغییر کرد.")
                return redirect("accounts:profile")

    return render(
        request,
        "accounts/profile.html",
        {
            "profile": profile,
            "profile_form": profile_form,
            "password_form": password_form,
        },
    )

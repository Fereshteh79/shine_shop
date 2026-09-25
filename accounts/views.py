# accounts/views.py

from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View

from .forms import LoginForm, OtpRequestForm, OtpVerifyForm, RegisterForm
from .otp import OTPError, issue_otp, verify_otp
from .services import AccountService

User = get_user_model()

# کلید سشن برای نگه‌داشتن شمارهٔ موبایل بین مرحلهٔ ۱ و ۲ ورود با کد پیامکی
OTP_SESSION_KEY = "GAPGPTMASKTOKEN9xp6dz76gznX1X"

# مدت اعتبار سشن در مرحلهٔ OTP: ۱۰ دقیقه
OTP_SESSION_TTL = 600


class RegisterView(View):
    """ثبت‌نام کاربر جدید + ورود خودکار پس از ساخت حساب."""

    template_name = "accounts/register.html"

    def _get_safe_next(self, request) -> str:
        """مقصد امن برای redirect — جلوگیری از open redirect."""
        next_url = request.POST.get("next") or request.GET.get("next") or ""

        if next_url and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
        ):
            return next_url

        return ""

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("shop:home")

        return render(request, self.template_name, {"form": RegisterForm()})

    def post(self, request):
        if request.user.is_authenticated:
            return redirect("shop:home")

        form = RegisterForm(request.POST)

        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        user = AccountService.create_user(form_data=form.cleaned_data)

        login(
            request,
            user,
            backend="django.contrib.auth.backends.ModelBackend",
        )

        messages.success(
            request,
            f"خوش آمدید {user.display_name} عزیز! حساب شما با موفقیت ساخته شد.",
        )

        return redirect(self._get_safe_next(request) or "shop:home")


class UserLoginView(LoginView):
    """ورود با نام کاربری / ایمیل / موبایل + رمز عبور."""

    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        messages.success(
            self.request,
            f"{form.get_user().display_name} عزیز، خوش برگشتی!",
        )
        return super().form_valid(form)


class UserLogoutView(LogoutView):
    """خروج از حساب کاربری."""

    next_page = "shop:home"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, "با موفقیت از حساب خود خارج شدید.")
        return super().dispatch(request, *args, **kwargs)


class OtpRequestView(View):
    """مرحلهٔ ۱ ورود با کد پیامکی — گرفتن شماره و ارسال کد."""

    template_name = "accounts/otp_request.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("shop:home")

        return render(request, self.template_name, {"form": OtpRequestForm()})

    def post(self, request):
        if request.user.is_authenticated:
            return redirect("shop:home")

        form = OtpRequestForm(request.POST)

        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        phone = form.cleaned_data["phone_number"]

        try:
            issue_otp(phone_number=phone)
        except OTPError as exc:
            form.add_error("phone_number", str(exc))
            return render(request, self.template_name, {"form": form})

        # ذخیرهٔ شماره در سشن با عمر محدود
        request.session[OTP_SESSION_KEY] = phone
        request.session.set_expiry(OTP_SESSION_TTL)

        messages.success(
            request, "کد تأیید به شمارهٔ شما پیامک شد."
        )
        return redirect("accounts:otp_verify")


class OtpVerifyView(View):
    """مرحلهٔ ۲ ورود با کد پیامکی — بررسی کد و ورود یا ثبت‌نام."""

    template_name = "accounts/otp_verify.html"

    def _build_username(self, phone: str) -> str:
        """ساخت username یکتا از روی شماره موبایل."""

        base = f"user_{phone[-6:]}"
        username = base
        counter = 1

        while User.objects.filter(username=username).exists():
            username = f"{base}{counter}"
            counter += 1

        return username

    def dispatch(self, request, *args, **kwargs):
        # اگر شماره‌ای در سشن نباشد، کاربر مستقیم این صفحه را باز کرده
        if OTP_SESSION_KEY not in request.session:
            messages.warning(
                request, "ابتدا شمارهٔ خود را وارد کنید."
            )
            return redirect("accounts:otp_request")

        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("shop:home")

        return render(
            request,
            self.template_name,
            # شمارهٔ استخراج‌شده را برای نمایش در template می‌فرستیم
            {"phone": request.session.get(OTP_SESSION_KEY, "")},
        )

    def post(self, request):
        if request.user.is_authenticated:
            return redirect("shop:home")

        phone = request.session.get(OTP_SESSION_KEY, "")
        form = OtpVerifyForm(request.POST)

        if not form.is_valid():
            return render(
                request,
                self.template_name,
                {"phone": phone, "form": form},
            )

        try:
            verify_otp(phone_number=phone, code=form.cleaned_data["code"])
        except OTPError as exc:
            form.add_error("code", str(exc))
            return render(
                request,
                self.template_name,
                {"phone": phone, "form": form},
            )

        # پیدا کردن یا ساختن کاربر
        try:
            user = User.objects.get(phone_number=phone)
        except User.DoesNotExist:
            user = User.objects.create_user(
                username=self._build_username(phone),
                phone_number=phone,
            )
            user.set_unusable_password()
            user.save(update_fields=["password"])

        login(
            request,
            user,
            backend="django.contrib.auth.backends.ModelBackend",
        )

        # پاک‌سازی سشن
        del request.session[OTP_SESSION_KEY]
        request.session.set_expiry(None)

        messages.success(
            request,
            f"{user.display_name} عزیز، خوش آمدید!",
        )
        return redirect("shop:home")

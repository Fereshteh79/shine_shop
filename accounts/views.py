from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.utils.crypto import get_random_string

from .forms import (
    LoginForm,
    OtpRequestForm,
    OtpVerifyForm,
    RegisterForm,
)
from .otp import OTPError, issue_otp, verify_otp
from .services import AccountService

User = get_user_model()

OTP_SESSION_KEY = "otp_phone_number"


class RegisterView(View):
    template_name = "accounts/register.html"

    def _get_safe_next(self, request) -> str:
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
    next_page = "shop:home"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, "با موفقیت از حساب خود خارج شدید.")

        return super().dispatch(request, *args, **kwargs)


class OtpRequestView(View):
    """مرحله ۱ — دریافت شماره موبایل و ارسال کد."""

    template_name = "accounts/otp_request.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("shop:home")

        return render(
            request,
            self.template_name,
            {"form": OtpRequestForm()},
        )

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

        request.session[OTP_SESSION_KEY] = phone
        request.session.set_expiry(600)  # ۱۰ دقیقه فرصت برای وارد کردن کد

        messages.info(request, f"کد ورود به شماره {phone} پیامک شد.")

        return redirect("accounts:otp_verify")


class OtpVerifyView(View):
    """مرحله ۲ — بررسی کد و ورود خودکار."""

    template_name = "accounts/otp_verify.html"

    def get(self, request, phone=None):
        if request.user.is_authenticated:
            return redirect("shop:home")

        user = User.objects.create_user(
            username=f"user_{phone[3:]}",
            phone_number=phone,
            password=get_random_string(16),
        )

        phone = request.session.get(OTP_SESSION_KEY)

        if not phone:
            messages.warning(request, "ابتدا شماره موبایل خود را وارد کنید.")
            return redirect("accounts:otp_request")

        return render(
            request,
            self.template_name,
            {"form": OtpVerifyForm(), "phone": phone},
        )

    def post(self, request):
        if request.user.is_authenticated:
            return redirect("shop:home")

        phone = request.session.get(OTP_SESSION_KEY)

        if not phone:
            messages.warning(request, "ابتدا شماره موبایل خود را وارد کنید.")
            return redirect("accounts:otp_request")

        form = OtpVerifyForm(request.POST)

        if not form.is_valid():
            return render(
                request,
                self.template_name,
                {"form": form, "phone": phone},
            )

        try:
            verify_otp(
                phone_number=phone,
                code=form.cleaned_data["code"],
            )
        except OTPError as exc:
            form.add_error("code", str(exc))
            return render(
                request,
                self.template_name,
                {"form": form, "phone": phone},
            )

        user = User.objects.filter(phone_number=phone).first()

        if user is None:
            # شماره معتبر است ولی حساب ندارد — با اطلاعات حداقلی ثبت‌نام خودکار
            user = User.objects.create_user(
                username=f"user_{phone[3:]}",  # ۸ رقم آخر به‌عنوان نام کاربری موقت
                phone_number=phone,
                password=User.objects.make_random_password(),
            )

            messages.success(
                request,
                "حساب شما با شماره موبایل ساخته شد؛ "
                "می‌توانید بعداً ایمیل و نام خود را کامل کنید.",
            )

        login(
            request,
            user,
            backend="django.contrib.auth.backends.ModelBackend",
        )

        del request.session[OTP_SESSION_KEY]

        messages.success(request, f"{user.display_name} عزیز، خوش آمدید!")

        return redirect("shop:home")

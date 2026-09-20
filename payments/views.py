from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views import View

from core.exceptions import PaymentError, ValidationError
from orders.selectors import get_user_order

from .forms import PaymentStartForm
from .selectors import get_user_payments
from .services import PaymentService


class PaymentListView(LoginRequiredMixin, View):
    template_name = "payments/payment_list.html"

    def get(self, request: HttpRequest):
        return render(
            request,
            self.template_name,
            {"payments": get_user_payments(request.user)},
        )


class PaymentStartView(LoginRequiredMixin, View):
    template_name = "payments/payment_start.html"

    def _get_order_or_404(self, request: HttpRequest, order_id: int):
        order = get_user_order(request.user, order_id)

        if order is None:
            raise Http404("سفارش مورد نظر یافت نشد.")

        return order

    def get(self, request: HttpRequest, order_id: int):
        order = self._get_order_or_404(request, order_id)

        return render(
            request,
            self.template_name,
            {"order": order, "form": PaymentStartForm()},
        )

    def post(self, request: HttpRequest, order_id: int):
        order = self._get_order_or_404(request, order_id)

        form = PaymentStartForm(request.POST)

        if not form.is_valid():
            return render(
                request,
                self.template_name,
                {"order": order, "form": form},
                status=400,
            )

        try:
            payment = PaymentService.create_payment(
                user=request.user,
                order=order,
                gateway_name=form.cleaned_data["gateway"],
                request=request,
            )

        except (PaymentError, ValidationError) as exc:
            messages.error(request, str(exc))
            return redirect("orders:detail", order_id=order.id)

        return redirect(payment.payment_url)


class PaymentCallbackView(View):
    """بازگشت از درگاه پرداخت — تأیید تراکنش و نمایش نتیجه."""

    def get(self, request: HttpRequest):
        authority = request.GET.get("Authority", "").strip()
        status = request.GET.get("Status", "").strip()

        try:
            payment = PaymentService.verify_payment(
                authority=authority,
                payment_status=status,
            )

        except PaymentError as exc:
            return render(
                request,
                "payments/payment_result.html",
                {
                    "success": False,
                    "message": str(exc),
                    "payment": None,
                },
                status=400,
            )

        if payment.is_successful:
            messages.success(request, "پرداخت شما با موفقیت انجام شد.")

            return redirect("orders:detail", order_id=payment.order_id)

        return render(
            request,
            "payments/payment_result.html",
            {
                "success": False,
                "message": payment.error_message or "پرداخت انجام نشد.",
                "payment": payment,
            },
        )

from decimal import Decimal, ROUND_HALF_UP

from django.shortcuts import redirect
from django.utils.http import url_has_allowed_host_and_scheme


def money(value) -> Decimal:
    return Decimal(value).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


def calculate_percentage(amount: Decimal, percentage: Decimal) -> Decimal:
    return money(amount * percentage / Decimal("100"))


def safe_redirect(request, target, fallback):
    if target and url_has_allowed_host_and_scheme(
            target,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
    ):
        return redirect(target)

    return redirect(fallback)

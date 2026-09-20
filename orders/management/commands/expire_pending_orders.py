from django.core.management.base import BaseCommand

from orders.services import OrderService


class Command(BaseCommand):
    help = "لغو سفارش‌های پرداخت‌نشده منقضی و آزادسازی موجودی آن‌ها."

    def handle(self, *args, **options):
        expired = OrderService.expire_pending_orders()

        self.stdout.write(
            self.style.SUCCESS(
                f"{expired} سفارش منقضی شد."
            )
        )

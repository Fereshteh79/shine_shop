class OrderStatus:
    PENDING = "pending"
    PAID = "paid"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

    CHOICES = (
        (PENDING, "در انتظار پرداخت"),
        (PAID, "پرداخت شده"),
        (PROCESSING, "در حال پردازش"),
        (SHIPPED, "ارسال شده"),
        (DELIVERED, "تحویل داده شده"),
        (CANCELLED, "لغو شده"),
    )


class PaymentStatus:
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"

    CHOICES = (
        (PENDING, "در انتظار"),
        (SUCCESS, "موفق"),
        (FAILED, "ناموفق"),
        (CANCELLED, "لغو شده"),
    )

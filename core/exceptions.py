class ServiceError(Exception):
    """Base exception for application services."""


class ValidationError(ServiceError):
    """Business validation error."""


class InsufficientStockError(ServiceError):
    """Raised when requested stock is unavailable."""


class PaymentError(ServiceError):
    """Raised when payment processing fails."""

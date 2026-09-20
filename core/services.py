from contextlib import contextmanager

from django.db import transaction


class BaseService:
    """Base class for application services."""

    @staticmethod
    @contextmanager
    def atomic():
        with transaction.atomic():
            yield

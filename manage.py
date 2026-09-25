#!/usr/bin/env python
"""ابزار خط فرمان Django برای پروژه Shine Shop."""
from __future__ import annotations

import os
import sys

DEFAULT_SETTINGS_MODULE = "shine_shop.settings"


def main() -> None:
    """اجرای دستورات مدیریتی Django."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", DEFAULT_SETTINGS_MODULE)

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Django در این محیط نصب نیست. مطمئن شوید virtualenv فعال است و "
            "'pip install -r requirements.txt' اجرا شده باشد."
        ) from exc

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()

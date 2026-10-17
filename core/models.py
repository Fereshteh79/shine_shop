"""مدلهای abstract مشترک پروژه.

توجه: `abstract = True` یعنی Django هیچ جدول و هیچ migrationی برای این کلاسها
نمیسازد؛ فقط کد مشترک به مدلهای دیگر ارث میرسد.
"""
from __future__ import annotations

from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    """مدل پایه با زمان ایجاد و آخرین ویرایش.

    نکتهٔ کلیدی: `save()` را طوری بازنویسی کردهایم که هر بار `update_fields`
    داده شود، `updated_at` **بهطور خودکار** به آن اضافه شود. این کار جلوی
    باگ رایج `save(update_fields=["stock"])` را میگیرد که در آن
    `updated_at` هرگز آپدیت نمیشود.
    """

    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField("آخرین ویرایش", auto_now=True)

    class Meta:
        abstract = True
        ordering = ("-created_at",)

    def save(self, *args, update_fields=None, **kwargs):
        if update_fields is not None:
            update_fields = set(update_fields)
            if not update_fields:
                # چیزی برای نوشتن نیست؛ از یک UPDATE بیفایده جلوگیری کن
                return
            update_fields.add("updated_at")
            update_fields.discard("created_at")  # auto_now_add نباید در update باشد
            update_fields = list(update_fields)

        return super().save(*args, update_fields=update_fields, **kwargs)

    def touch(self) -> None:
        """بهروزرسانی فقط `updated_at` بدون تغییر بقیهٔ فیلدها."""
        self.updated_at = timezone.now()
        self.save(update_fields=["updated_at"])

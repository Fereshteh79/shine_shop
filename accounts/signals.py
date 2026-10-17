"""سیگنال‌های اپ accounts."""

from __future__ import annotations

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile, User


@receiver(post_save, sender=User)
def create_user_profile(
        sender,
        instance: User,
        created: bool,
        **kwargs,
) -> None:
    """ساخت خودکار Profile پس از ایجاد کاربر."""

    if created:
        Profile.objects.get_or_create(user=instance)
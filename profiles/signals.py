# profiles/signals.py
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import UserProfile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    """유저 모델이 생성될 떄, 연결된 프로필을 자동으로 생성"""
    if created:
        UserProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    """유저 모델이 저장될 때, 프로필 정보도 함께 저장"""
    if hasattr(instance, "profile"):
        instance.profile.save()

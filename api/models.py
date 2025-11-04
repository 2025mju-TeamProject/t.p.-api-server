from django.db import models

# Create your models here.

from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    # Django의 기본 User 모델과 1:1로 연결
    # User가 회원가입하면 그에 딸린 Profile 객체 1개 생성
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')

    # 1. 'generate_profile'이 사용하는 정보
    nickname = models.CharField(max_length=50, blank=True, null=True)
    year = models.IntegerField(blank=True, null=True)
    month = models.IntegerField(blank=True, null=True)
    day = models.IntegerField(blank=True, null=True)
    hour = models.IntegerField(blank=True, null=True)
    minute = models.IntegerField(blank=True, null=True)
    gender = models.CharField(max_length=10, blank=True, null=True)
    job = models.CharField(max_length=50, blank=True, null=True)
    hobbies = models.JSONField(blank=True, null=True)  # 리스트는 JSONField로 저장
    mbti = models.CharField(max_length=10, blank=True, null=True)

    # 2. GPT가 생성하고, 사용자가 수정할 필드
    profile_text = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'{self.user.username}의 프로필'

# User가 생성될 때 Profile도 자동으로 생성
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    """User가 생성될 때, 그에 해당하는 Profile 객체를 자동으로 생성합니다."""
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    """User 객체가 저장될 때, 연결된 Profile 객체도 저장합니다."""
    try:
        instance.profile.save()
    except Profile.DoesNotExist:
        # (혹시 Profile이 없는 경우를 대비해 생성)
        Profile.objects.create(user=instance)
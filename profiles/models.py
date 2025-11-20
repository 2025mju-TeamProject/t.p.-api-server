from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models


class UserProfile(models.Model):
    """소개팅 서비스 전용 사용자 프로필"""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name='profile',
        on_delete=models.CASCADE,
        #primary_key=True,  # 사용자 PK를 그대로 프로필 PK로 사용
    )
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
    phone_number = models.CharField(max_length=20, unique=True, blank=True, null=True)
    # 2. GPT가 생성하고, 사용자가 수정할 필드
    profile_text = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Profile of {self.user.username}'

    def save(self, *args, **kwargs):
        if self.mbti:
            self.mbti = self.mbti.upper()
        super().save(*args, **kwargs)

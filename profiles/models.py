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
    birth_date = models.DateField(null=True, blank=True)  # 사주 계산 및 필터링 용도
    birth_time = models.TimeField(null=True, blank=True)
    profile_text = models.TextField(blank=True)  # AI 자동 생성 문구
    hobbies = models.JSONField(default=list, blank=True)  # 프론트에서 리스트 JSON으로 전달
    photos = models.JSONField(default=list, blank=True)  # 프로필 사진 경로나 URL 리스트
    job = models.CharField(max_length=100, blank=True)  # 직업 정보
    city = models.CharField(max_length=50, blank=True)  # 거주 도시 (시 단위)
    district = models.CharField(max_length=50, blank=True)  # 거주 구/동 단위
    mbti = models.CharField(
        max_length=4,
        blank=True,
        validators=[RegexValidator(regex=r'^[A-Z]{4}$', message='MBTI는 대문자 4글자여야 합니다.')],
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Profile of {self.user.username}'

    def save(self, *args, **kwargs):
        if self.mbti:
            self.mbti = self.mbti.upper()
        super().save(*args, **kwargs)

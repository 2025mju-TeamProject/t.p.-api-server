from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models


class UserProfile(models.Model):
    """소개팅 서비스 전용 사용자 프로필"""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name='profile',
        on_delete=models.CASCADE,
        # primary_key=True,  # 사용자 PK를 그대로 프로필 PK로 사용
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


# ✨ [중요] 아까 만드신 사진 업로드 기능을 위해 이 모델은 살려두는 것을 추천합니다.
# 만약 팀원이 사진 기능을 따로 구현했다면 지우셔도 됩니다.
class ProfileImage(models.Model):
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='profile_images/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.profile.user.username}의 사진 {self.id}"
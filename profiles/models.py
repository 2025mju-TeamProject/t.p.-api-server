from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.db.models.signals import post_save
from django.conf import settings
from django.dispatch import receiver


class UserProfile(models.Model):
    """소개팅 서비스 전용 사용자 프로필"""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name='profile',
        on_delete=models.CASCADE,
        # primary_key=True,  # 사용자 PK를 그대로 프로필 PK로 사용
    )

    # 1. 성별 선택
    gender = models.CharField(max_length=10, blank=True, null=True)

    # 2. 생년월일/태어난 시간, 분 선택
    year = models.IntegerField(blank=True, null=True)
    month = models.IntegerField(blank=True, null=True)
    day = models.IntegerField(blank=True, null=True)
    hour = models.IntegerField(blank=True, null=True)
    minute = models.IntegerField(blank=True, null=True)
    # '시간 모름' 경우
    birth_time_unknown = models.BooleanField(default=False)

    # 3. 관심사
    hobbies = models.JSONField(blank=True, null=True)  # 리스트는 JSONField로 저장

    # 4. MBTI (선택)
    mbti = models.CharField(max_length=10, blank=True, null=True)

    # 5. 직업 (선택)
    job = models.CharField(max_length=50, blank=True, null=True)

    # 6. 지역 (선택)
    # 시/도
    location_city = models.CharField(max_length=50, blank=True, null=True)
    # 시/군/구
    location_district = models.CharField(max_length=50, blank=True, null=True)

    # 7. 프로필 사진은 ProfileImage 모델에서 관리
    # 8. AI 생성 텍스트
    profile_text = models.TextField(blank=True, null=True)
    # 9. 사용자가 수정할 필드
    updated_at = models.DateTimeField(auto_now=True)

    # 회원가입에 사용할 휴대폰 번호
    phone_number = models.CharField(max_length=20, unique=True, blank=True, null=True)
    # 1. 'generate_profile'이 사용하는 정보
    nickname = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f'{self.user.username}의 프로필'

    def save(self, *args, **kwargs):
        if self.mbti:
            self.mbti = self.mbti.upper()
        super().save(*args, **kwargs)

class ProfileImage(models.Model):
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='profile_images/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.profile.user.username}의 사진 {self.id}"

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        # ✨ Profile -> UserProfile 로 변경
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    try:
        instance.profile.save() # related_name이 'profile'인 경우 유지
    except UserProfile.DoesNotExist: # ✨ 변경
        UserProfile.objects.create(user=instance)
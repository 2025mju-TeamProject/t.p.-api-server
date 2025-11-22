from django.db import models

# Create your models here.

from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

# class Profile(models.Model):
#     # Django의 기본 User 모델과 1:1로 연결
#     # User가 회원가입하면 그에 딸린 Profile 객체 1개 생성
#     user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
#
#     # 1. 성별 선택
#     gender = models.CharField(max_length=10, blank=True, null=True)
#
#     # 2. 생년월일/태어난 시간, 분 선택
#     year = models.IntegerField(blank=True, null=True)
#     month = models.IntegerField(blank=True, null=True)
#     day = models.IntegerField(blank=True, null=True)
#     hour = models.IntegerField(blank=True, null=True)
#     minute = models.IntegerField(blank=True, null=True)
#     # '시간 모름' 경우
#     birth_time_unknown = models.BooleanField(default=False)
#
#     # 3. 관심사
#     hobbies = models.JSONField(blank=True, null=True)  # 리스트는 JSONField로 저장
#
#     # 4. MBTI (선택)
#     mbti = models.CharField(max_length=10, blank=True, null=True)
#
#     # 5. 직업 (선택)
#     job = models.CharField(max_length=50, blank=True, null=True)
#
#     # 6. 지역 (선택)
#     # 시/도
#     location_city = models.CharField(max_length=50, blank=True, null=True)
#     # 시/군/구
#     location_district = models.CharField(max_length=50, blank=True, null=True)
#
#     # 7. 프로필 사진은 ProfileImage 모델에서 관리
#     # 8. AI 생성 텍스트
#     profile_text = models.TextField(blank=True, null=True)
#
#     # 회원가입에 사용할 휴대폰 번호
#     phone_number = models.CharField(max_length=20, unique=True, blank=True, null=True)
#     # 1. 'generate_profile'이 사용하는 정보
#     nickname = models.CharField(max_length=50, blank=True, null=True)
#
#     def __str__(self):
#         return f'{self.user.username}의 프로필'
#
# # 프로필 이미지 모델
# class ProfileImage(models.Model):
#     profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='images')
#     image = models.ImageField(upload_to='profile_images/') # 'images/profile_images/' 디렉에 저장됨
#     created_at = models.DateTimeField(auto_now_add=True)
#
#     def __str__(self):
#         return f"{self.profile.user.username}의 사진 {self.id}"

# User가 생성될 때 Profile도 자동으로 생성
# @receiver(post_save, sender=settings.AUTH_USER_MODEL)
# def create_user_profile(sender, instance, created, **kwargs):
#     """User가 생성될 때, 그에 해당하는 Profile 객체를 자동으로 생성합니다."""
#     if created:
#         Profile.objects.create(user=instance)
#
# @receiver(post_save, sender=settings.AUTH_USER_MODEL)
# def save_user_profile(sender, instance, **kwargs):
#     """User 객체가 저장될 때, 연결된 Profile 객체도 저장합니다."""
#     try:
#         instance.profile.save()
#     except Profile.DoesNotExist:
#         # (혹시 Profile이 없는 경우를 대비해 생성)
#         Profile.objects.create(user=instance)
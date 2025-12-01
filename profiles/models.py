# profiles/models.py

from django.db import models
from django.conf import settings

class UserProfile(models.Model):
    """소개팅 서비스 전용 사용자 프로필"""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name='profile',
        on_delete=models.CASCADE,
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

    # 위도
    latitude = models.FloatField(null=True, blank=True)
    # 경도
    longitude = models.FloatField(null=True, blank=True)

    # 7. 프로필 사진은 ProfileImage 모델에서 관리
    # 8. AI 생성 텍스트
    profile_text = models.TextField(blank=True, null=True)
    # 9. 사용자가 수정할 필드
    updated_at = models.DateTimeField(auto_now=True)
    photos = models.JSONField(default=list, blank=True)  # 프로필 사진 경로나 URL 리스트



    # 회원가입에 사용할 휴대폰 번호
    phone_number = models.CharField(max_length=20, unique=True, blank=True, null=True)
    # 1. 'generate_profile'이 사용하는 정보
    nickname = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f'{self.user.username}의 프로필'

class ProfileImage(models.Model):
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='profile_images/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):

        return f"{self.profile.user.username}의 사진 {self.id}"

class UserReport(models.Model):
    """사용자 신고 내역 모델"""

    # 신고 내용 카테고리
    REPORT_TYPE_CHOICES = [
        ('SPAM', '스팸'),
        ('ABUSE', '욕설 및 비하 발언'),
        ('ADULT', '나체 이미지 및 성적 행위'),
        ('FAKE', '사기 및 거짓'),
        ('OTHER', '기타'),
    ]

    # 신고 경로
    REPORT_SOURCE_CHOICES = [
        ('PROFILE', '프로필'),
        ('CHAT', '채팅방'),
    ]

    # 신고 상태
    REPORT_STATUS_CHOICES = [
        ('PENDING', '접수 대기'),
        ('RESOLVED', '처리 완료'),
        ('REJECTED', '반려됨'),
    ]

    # 신고자
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reports_sent')
    # 신고 당한 유저
    reported_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reports_received')

    reason = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    description = models.TextField(blank=True, null=True) # 상세 내용

    source = models.CharField(max_length=10, choices=REPORT_SOURCE_CHOICES, default='PROFILE')
    status = models.CharField(max_length=10, choices=REPORT_STATUS_CHOICES, default='PENDING')

    created_at = models.DateTimeField(auto_now_add=True)
    # 관리자 처리 시간
    processed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"[{self.get_status_display()}] {self.reporter} -> {self.reported_user} ({self.get_reason_display()})"

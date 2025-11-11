from django.db import models

# Create your models here.

from django.db import models
from django.conf import settings
from django.db.models import Q
from django.core.validators import RegexValidator

class ChatRoom(models.Model):
    # 'some_room_name' 같은 채팅방의 고유 이름
    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Message(models.Model):
    # 이 메시지가 속한 채팅방 (ChatRoom과 1:N 관계)
    room = models.ForeignKey(ChatRoom, related_name='messages', on_delete=models.CASCADE)
    # 메시지를 보낸 사람 (User와 1:N 관계)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sent_messages', on_delete=models.CASCADE)
    # 메시지 내용
    content = models.TextField()
    # 보낸 시간
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp'] # 메시지를 보낸 시간 순으로 정렬

    def __str__(self):
        return f'{self.sender.username} in {self.room.name}: {self.content[:20]}'

class Block(models.Model):
    """사용자 차단 관계 모델"""
    # 차단을 한 사용자
    blocker = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='blocking', on_delete=models.CASCADE)
    # 차단을 당한 사용자
    blocked = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='blocked_by', on_delete=models.CASCADE)
    # 차단한 시간
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # 한 사용자가 다른 사용자를 중복으로 차단하지 못 하게 설정
        unique_together = ('blocker', 'blocked')

    def __str__(self):
        return f'{self.blocker.username} blocked {self.blocked.username}'


class UserProfile(models.Model):
    """소개팅 앱용 사용자 프로필 확장 정보"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name='profile',
        on_delete=models.CASCADE,
    )
    birth_date = models.DateField()  # 생년월일(쿼리 최적화용 DateField)
    birth_time = models.TimeField()  # 태어난 시간(사주 계산 시 hour/minute 추출)
    profile_text = models.TextField(blank=True)  # AI가 생성한 프로필 문구
    #bio = models.TextField(blank=True)  #추가 프로필?
    hobbies = models.JSONField(default=list, blank=True)  # 취미 목록(프론트 JSON 그대로 저장)
    #preferences = models.JSONField(default=dict, blank=True)  # 이상형/취향 키-값 JSON
    photos = models.JSONField(default=list, blank=True)  # 프로필 사진 배열(경로/URL 리스트)
    mbti = models.CharField(
        max_length=4,
        blank=True,
        validators=[RegexValidator(regex=r'^[A-Z]{4}$', message='MBTI는 대문자 4글자여야 합니다.')],
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Profile of {self.user.username}'

    def save(self, *args, **kwargs):
        # MBTI는 항상 대문자 4글자로 저장
        if getattr(self, 'mbti', None):
            self.mbti = self.mbti.upper()
        super().save(*args, **kwargs)

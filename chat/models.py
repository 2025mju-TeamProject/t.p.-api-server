from django.db import models

# Create your models here.

from django.db import models
from django.conf import settings
from django.db.models import Q

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



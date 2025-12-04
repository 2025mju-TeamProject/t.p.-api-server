# chat/models.py

from django.db import models
from django.conf import settings

class ChatRoom(models.Model):
    """
    채팅 룸 생성 클래스
    'participants' : 이 방에 누가 있는지 직접 관리하는 DB 변수
    """
    # 방 이름 대신, User 목록 저장
    # ManyToManyField를 통해 이 방에 1번, 2번 유저가 있다는 관계가 저장됨
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name = 'chat_rooms' # 유저 입장에서 '내가 속한 방들'을 찾기 쉽게 이름 저장
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ChatRoom #{self.id}"

class Message(models.Model):
    # 이 메시지가 속한 채팅방 (ChatRoom과 1:N 관계)
    room = models.ForeignKey(ChatRoom, related_name='messages', on_delete=models.CASCADE)
    # 메시지를 보낸 사람 (User와 1:N 관계)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sent_messages', on_delete=models.CASCADE)
    # 메시지 내용
    content = models.TextField()
    # 이미지 파일 추가
    image = models.ImageField(upload_to='chat_images/%Y/%m%/%d/', null=True, blank=True)
    # 보낸 시간
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp'] # 메시지를 보낸 시간 순으로 정렬

    def __str__(self):
        # 텍스트가 없으면 "사진 메시지"라고 표시됨
        return f'{self.sender.username} in #{self.room.id}: {self.content[:20]}'

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
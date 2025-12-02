# interaction/models.py

from django.db import models
from django.conf import settings

class UserLike(models.Model):
    """
    유저 간의 관심 기록
    """
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='likes_sent'
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='likes_received'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # A가 B를 중복해서 관심 표시 못 함
        unique_together = ('sender', 'receiver')
        ordering = ['-created_at'] # 최신순 정렬

    def __str__(self):
        return f"{self.sender} -> {self.receiver}"
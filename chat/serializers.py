# chat/serializers.py

from rest_framework import serializers
from .models import Message

class MessageSerializer(serializers.ModelSerializer):
    # sender 필드를 기본 ID 대신 username으로 표시

    class Meta:
        model = Message
        fields = ['id', 'sender', 'content', 'image', 'timestamp']
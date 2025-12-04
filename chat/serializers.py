# chat/serializers.py

from rest_framework import serializers
from .models import Message

class MessageSerializer(serializers.ModelSerializer):
    message_id = serializers.IntegerField(source='id', read_only=True)
    class Meta:
        model = Message
        fields = ['message_id', 'sender', 'content', 'image', 'timestamp']
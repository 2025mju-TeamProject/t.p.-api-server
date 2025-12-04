# chat/admin.py

from django.contrib import admin
from .models import ChatRoom, Message, Block

@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_participants', 'created_at']

    def get_participants(self, obj):
        return ", ".join([user.username for user in obj.participants.all()])
    get_participants.short_description = '참여자'

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'room', 'sender', 'content_preview', 'timestamp']
    list_filter = ['room', 'sender']

    def content_preview(self, obj):
        return obj.content[:30] if obj.content else "(사진)"
    content_preview.short_description = '내용'

@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    list_display = ['id', 'blocker', 'blocked', 'created_at']
from django.contrib import admin

# Register your models here.

from django.contrib import admin
from .models import ChatRoom, Message, Block

@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'created_at']

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'room', 'sender', 'content', 'timestamp']
    list_filter = ['room', 'sender']
    search_fields = ['content']

@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    list_display = ['id', 'blocker', 'blocked', 'created_at']
    list_filter = ['blocker', 'blocked']

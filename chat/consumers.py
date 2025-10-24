import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import ChatRoom, Message # 모델 임포트
from django.contrib.auth import get_user_model # User 모델 임포트 ( sender 저장용 )

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if user.is_anonymous:
            await self.close()
            return

        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"

        # DB에서 채팅방을 찾거나, 없으면 새로 생성
        self.room = await self.get_or_create_room(self.room_name)

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name,
        )

    async def receive(self, text_data):
        payload = json.loads(text_data)
        message_content = payload.get("message", "").strip()
        if not message_content:
            return
        sender_user = self.scope["user"]

        await self.save_message(self.room, sender_user, message_content)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": message_content,
                "sender": sender_user.username,
            },
        )

    async def chat_message(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "message": event["message"],
                    "sender": event["sender"],
                }
            )
        )

    @database_sync_to_async
    def get_or_create_room(self, room_name):
        """DB에서 채팅방을 찾거나, 없으면 새로 생성함"""
        room, created = ChatRoom.objects.get_or_create(name=room_name)
        return room

    @database_sync_to_async
    def save_message(self, room, user, content):
        """채팅 메시지를 DB에 저장함"""
        Message.objects.create(room=room, sender=user, content=content)
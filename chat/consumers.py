# chat/consumers.py
import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import ChatRoom, Message, Block # 모델 임포트
from django.contrib.auth import get_user_model # User 모델 임포트 ( sender 저장용 )
from django.db.models import Q

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        user = self.scope["user"]
        if user.is_anonymous:
            await self.close()
            return

        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"

        # 차단 확인 로직
        try:
            user_id = [int(uid) for uid in self.room_name.split('-')]
            other_user_id = [uid for uid in user_id if uid != user.id][0]
            other_user = await self.get_user_instance(other_user_id)

            if await self.is_blocked(user, other_user):
                await self.close() # 차단했다면 연결 거부                return
        except Exception:
            await self.close() # room_name이 이상하거나 유저가 없으면 거부
            return

        # DB에서 채팅방을 찾거나, 없으면 새로 생성
        self.room = await self.get_or_create_room(self.room_name)

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
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
        # 1. 이벤트에서 데이터 추출
        # MessageUploadView에서 보낸 message, image 등을 여기서 받음
        message = event.get("message", "")
        sender = event.get("sender", "알 수 없음")
        image = event.get("image", None)
        timestamp = event.get("timestamp", "")

        await self.send(
            text_data=json.dumps(
                {
                    "message": message,
                    "sender": sender,
                    "image": image,
                    "timestamp": timestamp
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

    @database_sync_to_async
    def get_user_instance(self, user_id):
        """(비동기) ID로 유저 객체 가져오기"""
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    @database_sync_to_async
    def is_blocked(self, user1, user2):
        """(비동기) 두 사용자 간에 차단이 있는지 확인"""
        if user1 is None or user2 is None:
            return True # 유저가 없을 시, 차단으로 간주
        return Block.objects.filter(
            Q(blocker=user1, blocked=user2) |
            Q(blocker=user2, blocked=user1)
        ).exists()
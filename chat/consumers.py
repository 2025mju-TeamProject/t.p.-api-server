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

        # 1. 로그인 안 한 유저 거부
        if user.is_anonymous:
            await self.close()
            return

        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"

        try:
            # 2. 방 이름에서 유저 ID 추출 ("19-20' -> [19, 20])
            room_user_ids = [int(uid) for uid in self.room_name.split('-')]

            # 본인과의 채팅 방지
            if room_user_ids[0] == room_user_ids[1]:
                print(f"[접근 거부] 자기 자신과의 채팅은 지원하지 않습니다.")
                await self.close()
                return

            # 현재 접속한 유저가 방 멤버가 아니면 내쫓기
            if user.id not in room_user_ids:
                print(f"[접근 거부] User {user.id}는 {self.room_name} 방의 멤버가 아닙니다.")
                await self.close()
                return

            # 2. 상대방 ID 찾기
            # 내 ID가 0번째면 상대는 1번째, 내 ID가 1번째면 상대는 0번째
            if room_user_ids[0] == user.id:
                other_user_id = room_user_ids[1]
            else:
                other_user_id = room_user_ids[0]

            # 3. 상대방 유저 객체 가져오기
            other_user = await self.get_user_instance(other_user_id)

            # 상대방이 DB에 없을 경우
            if other_user is None:
                print(f" [입장 실패] 존재하지 않는 사용자(ID: {other_user_id})와의 채팅입니다.")
                await self.close()
                return

            # 3. 차단 확인 로직
            if await self.is_blocked(user, other_user):
                print(f"[차단됨] User {user.id}와 {other_user_id}는 차단 관계입니다.")
                await self.close() # 차단했다면 연결 거부
                return

        except (ValueError, IndexError):
            print(f"[오류] 잘못된 방 이름 형식: {self.room_name}")
            await self.close()
            return

        # 4. 검증 통과 -> 방 입장 및 연결 수락
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
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
        self.user = self.scope["user"]

        # 1. 로그인 안 한 유저 거부
        if self.user.is_anonymous:
            await self.close()
            return

        try:
            self.target_id = int(self.scope["url_route"]["kwargs"]["target_id"])
        except (ValueError, KeyError):
            print(f"[오류] 잘못된 URL 요청입니다.")
            await self.close()
            return

        # 4. 상대방 유저 객체 가져오기 및 존재 여부 확인
        self.target_user = await self.get_user_instance(self.target_id)

        # 본인과의 채팅 방지
        if self.target_id == self.user.id:
            print(f"[접근 거부] 자기 자신과의 채팅은 지원하지 않습니다.")
            await self.close()
            return

        self.target_user = await self.get_user_instance(self.target_id)

        # 상대방이 DB에 없을 경우
        if self.target_user is None:
            print(f" [입장 실패] 존재하지 않는 사용자(ID: {self.target_id})와의 채팅입니다.")
            await self.close()
            return

        # 3. 차단 확인 로직
        if await self.is_blocked(self.user, self.target_user):
            print(f"[차단됨] User {self.user.id}와 {self.target_id}는 차단 관계입니다.")
            await self.close()  # 차단했다면 연결 거부
            return

        # 현재 접속한 유저가 방 멤버가 아니면 내쫓기
        # if self.id not in room_user_ids:
        #     print(f"[접근 거부] User {user.id}는 {self.room_name} 방의 멤버가 아닙니다.")
        #     await self.close()
        #     return


        # 4. 검증 통과 -> 방 입장 및 연결 수락
        self.room = await self.get_or_create_room(self.user, self.target_user)

        self.room_group_name = f"chat_{self.room.id}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )
        await self.accept()
        print(f"[연결 성공] Room #{self.room.id} (User {self.user.id} <-> User {self.target_id})")

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name,
            )

    async def receive(self, text_data):
        """웹소켓으로 들어온 메시지를 처리하는 함수"""
        try:
            payload = json.loads(text_data)
            message_content = payload.get("message", "").strip()

            # 빈 메시지는 무시
            if not message_content:
                return

            # 1. DB에 저장
            new_msg = await self.save_message(self.room, self.user, message_content)

            # 2. 채팅방에 메시지 보내긱
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message": new_msg.content,
                    "sender": self.user.id,
                    "sender_name": self.user.username,  # 편의상 username 보냄
                    "image": None,  # 웹소켓 전송은 이미지 불가
                    "timestamp": str(new_msg.timestamp)
                }
            )
        except Exception as e:
            print(f" [WebSocket Error] {e}")

    async def chat_message(self, event):
        # 1. 이벤트에서 데이터 추출
        message = event.get("message", "")
        sender = event.get("sender", "알 수 없음")
        image = event.get("image", None)
        timestamp = event.get("timestamp", "")

        sender_name = event.get("sender_name", sender)

        await self.send(
            text_data=json.dumps(
                {
                    "message": message,
                    "sender": sender,
                    "sender_name": sender_name,
                    "image": image,
                    "timestamp": timestamp
                }
            )
        )

    @database_sync_to_async
    def get_or_create_room(self, user1, user2):
        """DB에서 채팅방을 찾거나, 없으면 새로 생성함"""
        room = ChatRoom.objects.filter(participants=user1).filter(participants=user2).first()

        if not room:
            room = ChatRoom.objects.create()
            room.participants.add(user1, user2)
        return room

    @database_sync_to_async
    def save_message(self, room, user, content):
        """채팅 메시지를 DB에 저장함"""
        msg = Message.objects.create(room=room, sender=user, content=content)
        return msg

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
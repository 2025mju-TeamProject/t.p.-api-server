import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ChatConsumer(AsyncWebsocketConsumer):
    # WebSocket 연결이 시작될 때 실행
    async def connect(self):
        # URL에서 상대방 user_id를 가져옴
        self.other_user_id = self.scope['url_route']['kwargs']['other_user_id']
        my_id = self.scope['user'].id

        # 두 user_id를 기반으로 고유한 채팅방 이름ㅇ르 생성 (id 순서 보장)
        if int(my_id) > int(self.other_user_id):
            self.room_name = f'{my_id}-{self.other_user_id}'
        else:
            self.room_name = f'{self.other_user_id}-{my_id}'

        self.room_group_name = f'chat_{self.room_name}'

        # 그룹(채팅방)에 참여
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # WebSocket 연결을 수락
        await self.accept()

    # WebSocket 연결이 끊어졌을 때 실행
    async def disconnect(self, close_code):
        # 그룹에서 탈퇴
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Client로부터 message를 받았을 때 실행
    async def reveive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # 같은 그룹에 있는 다른 Client들에게 message를 전송
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message', # 아래 chat_message 함수를 호출
                'message': message,
                'sender': self.scope['user'].username
            }
        )

        # Group으로부터 message를 받았을 때 실행 (위 group_send에서 호출)
        async def chat_message(self, event):
            message = event['message']
            sender = event['sender']

            # WebSocket을 통해 Client에게 JSON 형태로 message를 전송
            await self.send(text_data=json.dumps({
                'message': message,
                'sender': sender
            }))

# chat/views.py

import json
import openai
from django.http import Http404
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.conf import settings

# API 구현 위한 추가 모듈
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, permissions

# DB 설계를 위해 필요한 모델
from .models import ChatRoom, Message, Block
from .serializers import MessageSerializer
from profiles.models import UserProfile

# 채널 레이어
from channels.layers import get_channel_layer
# 비동기 코드를 동기에서 실행
from asgiref.sync import async_to_sync

User = get_user_model()
openai.api_key = settings.OPENAI_API_KEY

def get_personal_chat_room(user_a, user_b):
    """
    [헬퍼 함수] 두 유저(A, B)가 속한 1:1 채팅방을 찾거나, 없으면 만듭니다.
    DB 관계를 조회함
    """
    # 1. 두 유저가 모두 포함된 방을 찾습니다. (교집함)
    # participants에 user_a가 있고 user_b도 있는 방
    room = ChatRoom.objects.filter(participants=user_a).filter(participants=user_b).first()

    # 2. 방이 없으면 새로 생성
    if not room:
        room = ChatRoom.objects.create()
        room.participants.add(user_a, user_b)

    return room

class MessageSendView(APIView):
    """
    [POST] /api/chat/message/<int:target_id>/
    상대방(target_id)에게 메시지나 사진을 보냄
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, target_id):
        sender = request.user

        # 1. 상대방 유저 확인
        target_user = get_object_or_404(User, id=target_id)

        # 2. 자기 자신에게 보내기 방지
        if sender.id == target_id:
            return Response(
                {"error": "자기 자신과는 대화할 수 없습니다."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3. 헬퍼 함수를 통해 방을 가져옴 (없으면 자동 생성)
        room = get_personal_chat_room(sender, target_user)

        # 4. 차단 여부 확인
        is_blocked = Block.objects.filter(
            Q(blocker=sender, blocked=target_user) |
            Q(blocker=target_user, blocked=sender)
        ).exists()

        if is_blocked:
            return Response(
                {"error": "차단된 관계입니다."},
                status=status.HTTP_403_FORBIDDEN
            )

        # 5. 입력 데이터 확인
        image_file = request.FILES.get('image')
        content_text = request.data.get('message', '')

        if not image_file and not content_text:
            return Response(
                {"error": "내용을 입력해주세요."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 6. 메시지 저장
        new_msg = Message.objects.create(
            room=room,
            sender=sender,
            content=content_text,
            image=image_file
        )

        # 7. 웹소켓으로 실시간 알림 전송
        channel_layer = get_channel_layer()
        room_group_name = f"chat_{room.id}"

        image_url = new_msg.image.url if new_msg.image else None

        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                "type": "chat_message",
                "message_id": new_msg.id,
                "message": new_msg.content,
                "sender": sender.id,
                "sender_name": sender.username,
                "image": image_url,
                "timestamp": str(new_msg.timestamp)
            }
        )
        return Response(
            MessageSerializer(new_msg).data,
            status=status.HTTP_201_CREATED
        )

# 2. REST API views : 과거 메시지 내역
class MessageHistoryView(APIView):
    """
    특정 채팅방의 과거 메시지 내역을 불러오는 REST API
    URL 예 : /api/chat/history/<int:target_id>/
    """
    # IsAuthenticated: 로그인한 사용자만 이 API에 접근 가능함
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, target_id):
        target_user = get_object_or_404(User, id=target_id)

        # 1. 차단 확인
        is_blocked = Block.objects.filter(
            Q(blocker=request.user, blocked=target_user) |
            Q(blocker=target_user, blocked=request.user)
        ).exists()

        if is_blocked:
            return Response(
                {"error": "차단된 사용자외의 내역을 볼 수 없습니다."},
                status=status.HTTP_403_FORBIDDEN
            )

        # 2. 방 찾기
        room = ChatRoom.objects.filter(participants=request.user).filter(participants=target_user).first()

        if not room:
            # 대화한 적 없음
            return Response([], status=status.HTTP_200_OK)

        # 3. 메시지 가져오기
        messages = room.messages.all()
        serializer = MessageSerializer(messages, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

class ChatRoomListView(APIView):
    """
    내 토큰으로 내가 속한 채팅방 목록을 조회
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # 1. 내가 참여 중인 모든 방 조회
        my_rooms = ChatRoom.objects.filter(participants=user).prefetch_related('participants', 'messages')

        results = []
        for room in my_rooms:
            # 2. 상대방 찾기 (나를 제외한 나머지 1명)
            other_user = room.participants.exclude(id=user.id).first()

            # 상대방이 없으면 건너뜀 (건너뛰지말고 response값 만들기)
            if not other_user:
                continue

            # 3. 상대방 프로필 정보 가져오기
            other_nickname = other_user.username
            other_image = None
            try:
                profile = other_user.profile

                if profile.nickname:
                    other_nickname = profile.nickname
                if profile.images.exists():
                    other_image = profile.images.first().image.url
            except UserProfile.DoesNotExist:
                pass

            # 4. 마지막 메시지
            last_msg = room.messages.last()
            last_content = ""
            last_timestamp = room.created_at
            if last_msg:
                last_content = "사진" if (last_msg.image and not last_msg.content) else last_msg.content
                last_timestamp = last_msg.timestamp

            results.append({
                "room_id": room.id,  # 방 ID
                "other_user_id": other_user.id,  # 상대방 ID
                "other_nickname": other_nickname,
                "other_image": other_image,
                "last_message": last_content,
                "timestamp": last_timestamp
            })

        return Response(results, status=status.HTTP_200_OK)

# 3. REST API: 사용자 차단/해제
class BlockUserView(APIView):
    """
    사용자를 차단하거나 차단/해제하는 API
    - POST: 차단
    - DELETE: 차단 해제
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, user_id_to_block):
        blocker = request.user
        try:
            blocked = User.objects.get(id=user_id_to_block)
        except User.DoesNotExist:
            return Response(
                {"error": "차단할 사용자를 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND
            )

        if blocker == blocked:
            return Response(
                {"error": "스스로를 차단할 수 없습니다."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 이미 차단했는지 확인하고 없으면 생성
        block, created = Block.objects.get_or_create(blocker=blocker, blocked=blocked)

        if created:
            return Response(
                {"message": f"{blocked.username}님을 차단했습니다."},
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                {"message": "이미 차단한 사용자입니다."},
                status=status.HTTP_200_OK
            )

    def delete(self, request, user_id_to_block):
        """DELETE: user_id_to_block 사용자의 차단을 해제합니다."""
        blocker = request.user
        try:
            blocked = User.objects.get(id=user_id_to_block)
        except User.DoesNotExist:
            return Response(
                {"error": "차단 해제할 사용자를 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND
            )

        # 차단 기록을 찾아서 삭제
        count, _ = Block.objects.filter(blocker=blocker, blocked=blocked).delete()

        if count > 0:
            return Response(
                {"message": "차단 해제했습니다."},
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"error": "차단 기록이 없습니다."},
                status=status.HTTP_404_NOT_FOUND
            )


class ChatSuggestionView(APIView):
    """
    최근 10개 메시지를 참고해 3~4개 답변을 추천
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, target_id):
        user_id = request.user.id

        try:
            target_user = User.objects.get(id=target_id)
        except User.DoesNotExist:
            return Response(
                {"error": "상대방을 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND
            )

        room = ChatRoom.objects.filter(participants=request.user).filter(participants=target_user).first()

        if not room:
            return Response({"error": "대화 기록이 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        messages = list(
            Message.objects.filter(room=room)
            .order_by("-timestamp")
            .values("sender__id", "sender__username", "content")[:10][::-1]
        )

        if not messages:
            return Response(
                {"error": "대화 내용이 부족하여 추천할 수 없습니다."},
                status=status.HTTP_400_BAD_REQUEST
            )

        convo_text = "\n".join([f"{m['sender__username']}: {m['content']}" for m in messages])

        # 이름 정보
        user_nickname = request.user.username
        target_nickname = target_user.get_username()

        # 2. 마지막 메시지가 누구인지 확인
        last_message = messages[-1]
        is_last_sender_me = (last_message['sender__id'] == user_id)

        # 3. 상황에 따른 지시사항 분기 처리
        if is_last_sender_me:
            # 내가 마지막에 보내면 나에게 맞는 대화 추천
            situation_instruction = (
                f"중요: 마지막 메시지는 나({user_nickname})가 보낸 거야.\n"
                f"따라서 '상대방의 리액션(아하, 그렇구나 등)'을 추천하면 절대 안 돼.\n"
                f"이미 내가 보낸 메시지에 이어서 보낼 수 있는 '추가적인 멘트'나 '자연스러운 화제 전환', 혹은 '질문'을 추천해줘."
            )
        else:
            # 상대가 마지막에 보냄 -> 일반적인 답장 추천
            situation_instruction = (
                f"마지막 메시지는 상대방({target_nickname})이 보냈어.\n"
                f"이에 대한 적절한 리액션이나 답장을 추천해줘."
            )

        system_prompt_lines = [
            f"너는 User ID {user_id}(닉네임: {user_nickname})의 연애 코치이야.",
            f"상대방은 User ID {target_id}(닉네임: {target_nickname})이야.",
            "너는 친근하고 예의있는 대화 코치야. 개인정보 요구나 공격적인 표현은 피한다.",
            "사용자가 다음 메시지로 보낼 수 있는 자연스러운 답변을 3~4개 제안해줘.",
            "각 제안은 한두 문장으로 짧게 해줘.",
            "여기는 소개팅앱이고, 남녀가 서로 대화하는 상황이야.",
            "너는 최대한 대화가 잘 이루어질 수 있도록 도와줘야 해.",
            f"최대한 {user_nickname}의 말투랑 비슷하게 하되, 대화에 유익한 방향으로 이끌어줘 말투가 문제라면 조금 다르게 해도 좋아."
        ]
        system_prompt = "\n".join(system_prompt_lines)
        profile_lines = []

        def summary_for(user_obj):
            try:
                p = user_obj.profile
            except UserProfile.DoesNotExist:
                return None
            hobbies = ", ".join(p.hobbies) if p.hobbies else None
            parts = []
            if p.nickname:
                parts.append(f"닉네임: {p.nickname}")
            if p.gender:
                parts.append(f"성별: {p.gender}")
            if p.location_city or p.location_district:
                parts.append(f"지역: {p.location_city or ''} {p.location_district or ''}".strip())
            if p.job:
                parts.append(f"직업: {p.job}")
            if p.mbti:
                parts.append(f"MBTI: {p.mbti}")
            if hobbies:
                parts.append(f"관심사: {hobbies}")
            return "; ".join(parts) if parts else None

        if len(messages) < 10:
            user_summary = summary_for(request.user)
            target_summary = summary_for(target_user)

            if user_summary or target_summary:
                profile_lines.append("참고 프로필 정보:")
                if user_summary:
                    profile_lines.append(f"- 나: {user_summary}")
                if target_summary:
                    profile_lines.append(f"- 상대: {target_summary}")

        profile_block = "\n".join(profile_lines)

        user_prompt = (
            f"상황 설정:\n"
            f"- 나 (User ID {user_id}): {user_nickname}\n"
            f"- 상대방 (User ID {target_id}): {target_nickname}\n\n"
            "다음은 최근 채팅 내역이야.\n"
            f"{convo_text}\n\n"
            f"{profile_block}\n\n" if profile_block else f"다음은 최근 채팅 내역이야.\n{convo_text}\n\n"
        ) + (
            f"\n{situation_instruction}\n\n"
            f"반드시 {user_id}(나)가 보낼 적절한 답변 3개를 추천해줘.\n"
            f"마지막에 누가 말했든 상관없이, 무조건 User {user_id}의 입장에서 답장을 만들어야 해.\n"
            'JSON 배열 형태로만 응답해: ["제안1", "제안2", "제안3"]. '
            "각 제안은 짧게."
        )

        try:
            completion = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=300,
                temperature=0.7,
            )
            content = completion.choices[0].message.content
            suggestions = json.loads(content)
            if not isinstance(suggestions, list):
                raise ValueError("Suggestions must be a list")
        except Exception as e:
            return Response(
                {"error": f"추천 생성에 실패했습니다: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            {"suggestions": suggestions},
            status=status.HTTP_200_OK
        )
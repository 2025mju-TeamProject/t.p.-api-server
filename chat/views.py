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

User = get_user_model()
openai.api_key = settings.OPENAI_API_KEY

# 1. 채팅방 입장 뷰
@login_required
def chat_room(request, other_user_id):
    """
    두 사용자 ID를 기반으로 1:1 채팅방 페이지를 렌더링 함
    """
    try:
        my_id = int(request.user.id)
        other_user_id = int(other_user_id)
    except ValueError:
        raise Http404("유효하지 않은 사용자 ID입니다.")

    if my_id == other_user_id:
        raise Http404("다른 사용자와의 채팅만 지원합니다.")

    # 차단 확인 로직
    other_user = get_object_or_404(User, id=other_user_id)

    # 차단 상태 확인
    is_blocked = Block.objects.filter(
        Q(blocker=request.user, blocked=other_user) | # 내가 차단함
        Q(blocker=other_user, blocked=request.user)   # 상대방이 날 차단함
    ).exists()

    if is_blocked:
        # 차단한 경우, 404 에러 띄우고 채팅방 입장 막음
        raise Http404("차단했거나 차단된 사용자와의 채팅방입니다.")


    room_name = "-".join(sorted([str(my_id), str(other_user_id)]))
    room, _ = ChatRoom.objects.get_or_create(name=room_name)

    # 이전 대화 내용 가져오기
    prev_messages = [
        {
            'sender': m.sender.username,
            'content': m.content,
            'timestamp': m.timestamp.isoformat()
        }
        for m in room.messages.order_by('timestamp')
    ]

    return render(
        request,
        "chat/chat_room.html",
        {
            "other_user_id": other_user_id,
            "room_name": room_name,
            "prev_messages": prev_messages,
        },
    )

# 2. REST API views : 과거 메시지 내역
class MessageHistoryView(APIView):
    """
    특정 채팅방의 과거 메시지 내역을 불러오는 REST API
    URL 예 : /api/chat/message/2-5/
    """
    # IsAuthenticated: 로그인한 사용자만 이 API에 접근 가능함
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, room_name):
        """
        채팅방 이름(room_name)으로 과거 메시지 조회함
        """
        try:
            user_ids = [int(uid) for uid in room_name.split('-')]
            # room_name에서 내 ID각 아닌 다른 ID를 찾음
            other_user_id = [uid for uid in user_ids if uid != request.user.id][0]
            other_user = User.objects.get(id=other_user_id)

            is_blocked = Block.objects.filter(
                Q(blocker=request.user, blocked=other_user) |
                Q(blocker=other_user, blocked=request.user)
            ).exists()

            if is_blocked:
                return Response(
                    {"error": "차단된 사용자와의 내역을 볼 수 없습니다."},
                    status=status.HTTP_403_FORBIDDEN
                )
        except Exception:
            return Response(
                {"error": "채팅방 또는 사용자를 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            # 1. URL로 받은 room_name을 이용해 채팅방 찾음(ChatRoom 모델은 consumers.py에서 get_or_create_room으로 생성함)
            room = ChatRoom.objects.get(name=room_name)

            # 2. 이 API를 요청한 사용자가 해당 채팅방의 참여자 맞는지 판단(room_name은 "ID1-ID2" 형식으로 파싱)
            allowed_users = [int(uid) for uid in room.name.split('-')]
            if request.user.id not in allowed_users:
                return Response(
                    {"error": "이 채팅방에 접근할 권한이 없습니다."},
                    status=status.HTTP_403_FORBIDDEN
                )

            # 3. 해당 채팅방의 모든 메시지를 가져옴
            messages = room.messages.all()

            # 4. Serializer를 통해 메시지 목록을 JSON으로 변환함
            serializer = MessageSerializer(messages, many=True)

            return Response(serializer.data, status=status.HTTP_200_OK)

        except ChatRoom.DoesNotExist:
            # 아직 대화가 시작 안 돼서 ChatRoom 없는 경우
            return Response([], status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"메시지를 불러오는 중 오류 발생: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# 3. REST API: 사용자 차단/해제
class BlockUserView(APIView):
    """
    사용자를 차단하거나 차단 해제하는 API
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
        block, created = Block.objects.get_or_create(blocker=blocker, blocked= blocked)

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
        deleted_count, _ = Block.objects.filter(blocker=blocker, blocked=blocked).delete()

        if deleted_count > 0:
            return Response(
                {"message": f"{blocked.username}님을 차단 해제했습니다."},
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

    def post(self, request, room_name):
        try:
            room = ChatRoom.objects.get(name=room_name)
        except ChatRoom.DoesNotExist:
            return Response(
                {"error": "채팅방이 없습니다."},
                status=status.HTTP_404_NOT_FOUND
            )

        allowed_users = [int(uid) for uid in room.name.split("-")]
        if request.user.id not in allowed_users:
            return Response(
                {"error": "이 채팅방에 접근할 수 없습니다."},
                status=status.HTTP_403_FORBIDDEN
            )

        messages = list(
            Message.objects.filter(room=room)
            .order_by("-timestamp")
            .values("sender__username", "content")[:10][::-1]
        )
        convo_text = "\n".join([f"{m['sender__username']}: {m['content']}" for m in messages]) or "(대화 없음)"

        system_prompt_lines = [
            "너는 친근하고 예의있는 대화 코치야. 개인정보 요구나 공격적인 표현은 피한다.",
            "사용자가 다음 메시지로 보낼 수 있는 자연스러운 답변을 3~4개 제안해줘.",
            "각 제안은 한두 문장으로 짧게 해줘.",
            "여기는 소개팅앱이고, 남녀가 서로 대화하는 상황이야.",
            "너는 최대한 대화가 잘 이루어질 수 있도록 도와줘야 해.",
            "최대한 sender의 말투랑 비슷하게 하되, 대화에 유익한 방향으로 이끌어줘 말투가 문제라면 조금 다르게 해도 좋아."
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
            other_id = [uid for uid in allowed_users if uid != request.user.id]
            other_user = User.objects.filter(id=other_id[0]).first() if other_id else None
            my_summary = summary_for(request.user)
            other_summary = summary_for(other_user) if other_user else None
            if my_summary or other_summary:
                profile_lines.append("참고 프로필 정보:")
                if my_summary:
                    profile_lines.append(f"- 나: {my_summary}")
                if other_summary:
                    profile_lines.append(f"- 상대: {other_summary}")

        profile_block = "\n".join(profile_lines)

        user_prompt = (
            "다음은 최근 채팅 내역이야.\n"
            f"{convo_text}\n\n"
            f"{profile_block}\n\n" if profile_block else f"다음은 최근 채팅 내역이야.\n{convo_text}\n\n"
        ) + (
            "다음 메시지로 보낼 수 있는 자연스러운 답변을 3개 제안해줘. "
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
                temperature=0.8,
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


class ChatRoomListView(APIView):
    """
    내 토큰으로 내가 속한 채팅방 목록을 조회
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user_id = request.user.id
            rooms = []

            # 내 ID가 포함된 방 이름 검색
            qs = ChatRoom.objects.filter(name__contains=str(user_id))

            for room in qs:
                try:
                    ids = [int(x) for x in room.name.split("-")]

                    if user_id not in ids:
                        continue

                    # 상대방 ID 추출
                    other_ids = [i for i in ids if i != user_id]
                    other_id = other_ids[0] if other_ids else user_id

                    # 상대방 프로필 정보 추가 (프론트엔드 편의성)
                    other_nickname = "알 수 없는 사용자"
                    other_image = None

                    try:
                        target_profile = UserProfile.objects.get(user_id=other_id)
                        other_nickname = target_profile.nickname
                        if target_profile.images.exists():
                            other_image = target_profile.images.first().image.url
                    except UserProfile.DoesNotExist:
                        pass

                    rooms.append({
                        "room_name": room.name,
                        "other_user_id": other_id,
                        "other_nickname": other_nickname,
                        "other_image": other_image
                    })

                except ValueError:
                    continue

            return Response(rooms, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

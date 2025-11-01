from django.http import Http404
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Q

# API 구현 위한 추가 모듈
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

# DB 설계를 위해 필요한 모델
from .models import ChatRoom, Message, Block
from .serializers import MessageSerializer

User = get_user_model()

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

    return render(
        request,
        "chat/chat_room.html",
        {
            "other_user_id": other_user_id,
            "room_name": room_name,
        },
    )

# 2. REST API views : 과거 메시지 내역
class MessageHistoryView(APIView):
    """
    특정 채팅방의 과거 메시지 내역을 불러오는 REST API
    URL 예 : /api/chat/message/2-5/
    """
    # IsAuthenticated: 로그인한 사용자만 이 API에 접근 가능함
    permissions_classes = [permissions.IsAuthenticated]

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
                return Response({"error": "차단된 사용자와의 내역을 볼 수 없습니다."}, status=status.HTTP_403_FORBIDDEN)
        except Exception:
            return Response({"error": "채팅방 또는 사용자를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        try:
            # 1. URL로 받은 room_name을 이용해 채팅방 찾음(ChatRoom 모델은 consumers.py에서 get_or_create_room으로 생성함)
            room = ChatRoom.objects.get(name=room_name)

            # 2. 이 API를 요청한 사용자가 해당 채팅방의 참여자 맞는지 판단(room_name은 "ID1-ID2" 형식으로 파싱)
            allowed_users = [int(uid) for uid in room.name.split('-')]
            if request.user.id not in allowed_users:
                return Response({"error": "이 채팅방에 접근할 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)

            # 3. 해당 채팅방의 모든 메시지를 가져옴
            messages = room.messages.all()

            # 4. Serializer를 통해 메시지 목록을 JSON으로 변환함
            serializer = MessageSerializer(messages, many=True)

            return Response(serializer.data, status=status.HTTP_200_OK)

        except ChatRoom.DoesNotExist:
            # 아직 대화가 시작 안 돼서 ChatRoom 없는 경우
            return Response([], status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"메시지를 불러오는 중 오류 발생: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# 3. REST API: 사용자 차단/해제
class BlockUserView(APIView):
    """
    사용자를 차단하거나 차단 해제하는 API
    """
    permissions_classes = [permissions.IsAuthenticated]

    def post(self, request, user_id_to_block):
        """POST: user_id_to_block 사용자를 차단합니다."""
        blocker = request.user
        try:
            blocked = User.objects.get(id=user_id_to_block)
        except User.DoesNotExist:
            return Response({"error": "차단할 사용자를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        if blocker == blocked:
            return Response({"error": "스스로를 차단할 수 없습니다."}, status=status.HTTP_400_BAD_REQUEST)

        # 이미 차단했는지 확인하고 없으면 생성
        block, created = Block.objects.get_or_create(blocker=blocker, blocked= blocked)

        if created:
            return Response({"message": f"{blocked.username}님을 차단했습니다."}, status=status.HTTP_21_CREATED)
        else:
            return Response({"message": "이미 차단한 사용자입니다."}, status=status.HTTP_200_OK)

    def delete(self, request, user_id_to_block):
        """DELETE: user_id_to_block 사용자의 차단을 해제합니다."""
        blocker = request.user
        try:
            blocked = User.objects.get(id=user_id_to_block)
        except User.DoesNotExist:
            return Response({"error": "차단 해제할 사용자를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        # 차단 기록을 찾아서 삭제
        deleted_count, _ = Block.objects.filter(blocker=blocker, blocked=blocked).delete()

        if deleted_count > 0:
            return Response({"message": f"{blocked.username}님을 차단 해제했습니다."}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "차단 기록이 없습니다."}, status=status.HTTP_404_NOT_FOUND)

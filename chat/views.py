from django.core.serializers import serialize
from django.http import Http404
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# API 구현 위한 추가 모듈
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import ChatRoom, Message
from .serializers import MessageSerializer

@login_required  # 로그인이 필요한 뷰
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


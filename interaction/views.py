# interaction/views.py

from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import UserLike
from .serializers import UserLikeSerializer

User = get_user_model()

# API처럼 구현하면 안 되나 + url 설정해야되지않나
class UserLikeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, receiver_id):
        """
        [POST] 특정 유저에게 하트 보내기 / 취소(토글)
        """
        sender = request.user
        receiver = get_object_or_404(User, id=receiver_id)

        # 1. 셀프 하트 방지
        if sender == receiver:
            return Response(
                {"error": "자신에게 보낼 수 없습니다."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. 이미 보냈는지 확인 (있으면 취소, 없으면 생성)
        like_obj, created = UserLike.objects.get_or_create(sender=sender, receiver=receiver)

        if not created:
            like_obj.delete()
            return Response(
                {"message": "하트를 취소했습니다."},
                status=status.HTTP_200_OK
            )

        # 3. 하트 생성 성공하면 푸시 알림 발송 시뮬레이션
        try:
            sender_nick = sender.profile.nickname
        except:
            sender_nick = "알 수 없는 사용자"
        msg = f"{sender_nick}님에게 하트를 받았어요. 여기를 클릭하고 프로필을 확인해보세요!"
        print(f"[PUSH 전송] To: {receiver.id} / Msg: {msg}")  # 여기에 나중에 FCM 코드 넣음

        return Response(
            {"message": "하트를 보냈습니다."},
            status=status.HTTP_201_CREATED
        )

class LikeListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """
        [GET] 관림 목록 조회
        ?type=sent (내가 보낸 거) / ?type=received (내가 받은 거)
        """
        list_type = request.query_params.get('type', 'received')

        if list_type == 'sent':
            likes = UserLike.objects.filter(sender=request.user).select_related('receiver__profile')
        else:
            likes = UserLike.objects.filter(receiver=request.user).select_related('sender__profile')

        serializer = UserLikeSerializer(likes, many=True, context={'request' : request})
        return Response(serializer.data, status=status.HTTP_200_OK)
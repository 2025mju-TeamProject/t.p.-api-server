# interaction/serializers.py

from rest_framework import serializers

from .models import UserLike
from profiles.serializers import SimpleProfileSerializer

class UserLikeSerializer(serializers.ModelSerializer):
    """
    좋아요 목록 조회 시 상대방의 간단 정보(닉네임, 프로필 사진)를 함께 반환
    """
    target_profile = serializers.SerializerMethodField()

    class Meta:
        model = UserLike
        fields = ['id', 'created_at', 'target_profile']

    def get_target_profile(self, obj):
        # 목록의 성격에 따라 '상대방'이 누구인지 판단
        request = self.context.get('request')
        if request and obj.sender == request.user:
            target_user = obj.receiver # 내가 보내면 받는 사람이 타겟
        else:
            target_user = obj.sender # 내가 받으면 보낸 사람이 타겟

        try:
            return SimpleProfileSerializer(target_user.profile).data
        except Exception as e:
            return None
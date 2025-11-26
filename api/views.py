# api/views.py

import openai
import json
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.request import Request

from .saju_compatibility import calculate_compatibility_score

User = get_user_model()

# settings.py에서 API 키 불러옴
openai.api_key = settings.OPENAI_API_KEY

# 1. 사주 궁합 점수 조회 API
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def check_saju_compatibility(request, target_id):
    """
    [GET] ('api/match/score/<target_id>/'
    나와 상대방의 사주 궁합 점수 반환
    """
    try:
        # 1. 내 프로필 가져오기
        try:
            me = request.user.profile
        except AttributeError:
            return Response(
                {"error": "내 프로필이 존재하지 않습니다"},
                status=status.HTTP_404_NOT_FOUND
            )

        # 2. 상대방 프로필 가져오기
        target_user = get_object_or_404(User, id=target_id)
        try:
            target = target_user.profile
        except AttributeError:
            return Response(
                {"error": "상대방의 프로필이 존재하지 않습니다."},
                status=status.HTTP_404_NOT_FOUND
            )

        # 3. 본인과의 궁합 조회 예외 처리
        if request.user.id == target_id:
            return Response(
                {"error": "자신과의 궁합은 볼 수 없습니다."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 4. 궁합 점수 계산
        score = calculate_compatibility_score(me, target)

        return Response({
            "my_nickname": me.nickname,
            "partner_nickname": target.nickname,
            "compatibility_score": score,
            "message": "사주 궁합 분석이 완료되었습니다."
        }, status=status.HTTP_200_OK)
    except Exception as e:
        print(f"궁합 분석 중 오류 발생: {e}")
        return Response(
            {"error": "분석 중 오류 발생했습니다."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
# 2. AI 기반 궁합/취향 분석 리포트 제공 기능 (향후 개발 예정)
@api_view(['POST'])
def generate_compatibility_report(request: Request) -> Response:
     """
     두 사용자의 전체 정보를 받아 AI가 관계 분석 리포트를 생성합니다. (구현 예정)
     """
# TODO: 아래 로직을 실제로 구현해야 합니다.
# 1. 두 사용자의 전체 정보(user1, user2)를 request.data에서 가져옵니다.
#    각 사용자 정보에는 생년월일시분, 취미, MBTI 등이 모두 포함되어야 합니다.
# 2. 각 사용자의 생년월일시분 정보로 calculate_saju()를 각각 호출하여 사주 데이터를 얻습니다.
# 3. 두 사용자의 사주 데이터, 취미, MBTI를 모두 종합하여 AI 프롬프트를 구성합니다.
# 4. OpenAI API를 호출하여 리포트를 생성하고 반환합니다.
pass # 아직 기능이 구현되지 않았으므로 비워둡니다.


# 3. AI 기반 대화 어시스턴트 기능 (향후 개발 예정)
@api_view(['POST'])
def generate_conversation_starter(request: Request) -> Response:
    """
    두 사용자의 정보를 바탕으로 대화를 시작할 질문을 생성합니다. (구현 예정)
    """
# TODO: 아래 로직을 실제로 구현해야 합니다.
# 1. 두 사용자의 정보(user1, user2)를 request.data에서 가져옵니다.
# 2. 두 사용자의 취미, MBTI, (선택적으로) 사주 정보를 조합하여 AI 프롬프트를 구성합니다.
# 3. OpenAI API를 호출하여 질문을 생성하고 반환합니다.
pass # 아직 기능이 구현되지 않았으므로 비워둡니다.


# 4. 사주 정보 조회 API (독립적인 유틸리티 함수)
# @api_view(['POST'])
# def get_saju_api(request: Request) -> Response:
#     """
#     사용자의 생년월일시분 정보를 받아 사주팔자를 계산하고 반환합니다.
#     """
#     data = request.data
#     try:
#         year = int(data['year'])
#         month = int(data['month'])
#         day = int(data['day'])
#
#         # '시간 모름' 로직
#         unknown_val = data.get('birth_time_unknown')
#
#         if unknown_val == 'true' or unknown_val is True:
#             # 시간을 모르면 00시 00분으로 설정
#             hour = 0
#             minute = 0
#         else:
#             hour = int(data.get('hour', 0))
#             minute = int(data.get('minute', 0))
#
#     except (KeyError, ValueError, TypeError):
#         return Response({"error": "필수 정보가 누락되었거나, 데이터 형식이 올바르지 않습니다."}, status=status.HTTP_400_BAD_REQUEST)
#
#     # 사주 계산
#     saju_data = calculate_saju(year, month, day, hour, minute)
#
#     if "error" in saju_data:
#         return Response(saju_data, status=status.HTTP_400_BAD_REQUEST)
#
#     return Response(saju_data, status=status.HTTP_200_OK)

# TODO:
# 회원가입했을 때,
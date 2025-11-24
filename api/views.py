import openai
import json
from django.conf import settings

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.decorators import api_view
from rest_framework.request import Request

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
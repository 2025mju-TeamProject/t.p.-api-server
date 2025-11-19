import openai
from django.conf import settings
from django.http import JsonResponse

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework_simplejwt.views import TokenObtainPairView

from .saju_calculator import calculate_saju
from .models import Profile
from .serializers import (
    ProfileSerializer,
    ProfileTextUpdateSerializer,
    UserRegistrationSerializer, MyTokenObtainPairSerializer
)


# settings.py에서 API 키를 불러옵니다.
openai.api_key = settings.OPENAI_API_KEY


# 1. 프로필 관리 View (조회, AI 프로필 생성, 수동 수정)
"""
로그인한 사용자의 프로필을 다루는 View
- GET: 내 프로필 정보 조회
- POST: 내 정보로 AI 프로필 생성
- PATCH: 사용자가 AI 프로필 텍스트 수정
"""
class ProfileView(APIView): # (조회, AI 생성, 수동 수정)
    permission_classes = [permissions.IsAuthenticated] # 로그인 필수


    def get(self, request):
        """
        [GET] 로그인한 사용자의 프로필 정보를 반환
        """
        profile = request.user.profile
        serializer = ProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """
        [POST] 사용자의 기본 정보로 AI 프로필을 생성 DB에 저장
        """
        profile = request.user.profile
        data = request.data

        try:
            profile.nickname = data['nickname']
            profile.year = int(data['year'])
            profile.month = int(data['month'])
            profile.day = int(data['day'])
            profile.hour = int(data['hour'])
            profile.minute = int(data['minute'])
            profile.gender = data['gender']
            profile.job = data['job']
            # 선택 정보 추출
            profile.hobbies = data.get('hobbies')
            profile.mbti = data.get('mbti')

            if profile.hobbies and not isinstance(profile.hobbies, list):
                return Response({'error': '취미(hobbies)는 반드시 배열리스트 형태여야 합니다.'}, status=status.HTTP_400_BAD_REQUEST)

        except (KeyError, ValueError, TypeError):
            return Response({"error": "필수 정보가 누락되었거나, 데이터 형식이 올바르지 않습니다."}, status=status.HTTP_400_BAD_REQUEST)

        saju_data = calculate_saju(profile.year, profile.month, profile.day, profile.hour, profile.minute)
        if "error" in saju_data:
            return Response(saju_data, status=status.HTTP_400_BAD_REQUEST)

        my_saju_pillar = saju_data.get('day_pillar')

        # AI 프롬프트 동적 구성
        prompt_lines = [
            "아래 정보를 바탕으로, 데이팅 앱에서 사용할 매력적이고 진솔한 자기소개 문구를 200자 내외로 자연스럽게 작성해줘.",
            "특히 '타고난 사주 성향' 정보를 참고해서 그 사람의 성격이 은은하게 드러나도록 문장을 만들어 줘.",
            "",
            f"- 닉네임: {profile.nickname}",
            f"- 성별: {profile.gender}",
            f"- 직업: {profile.job}",
            f"- 타고난 사주 성향 (일주): {my_saju_pillar}"
        ]
        if profile.hobbies:
            prompt_lines.append(f"- 취미: {', '.join(profile.hobbies)}")
        if profile.mbti:
            prompt_lines.append(f"- MBTI: {profile.mbti}")
        prompt_lines.extend(["", "- 톤앤매너: 친근하고 긍정적인 느낌, 약간의 유머와 센스 포함"])
        prompt = "\n".join(prompt_lines)

        try:
            # OpenAI API 호출
            response = openai.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system",
                     "content": "You are a creative assistant who is an expert in writing appealing dating app profiles based on personality and Saju."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=300
            )
            profile_text = response.choices[0].message.content
            cleaned_profile = profile_text.strip().strip('"')

            profile.profile_text = cleaned_profile
            profile.save() # 모든 정보(기본 정보 + GPT 텍스트)를 DB에 최종 저장

            serializer = ProfileSerializer(profile)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'error': f'AI 프로필 생성에 실패했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request):
        """
        [PATCH] 로그인한 사용자의 프로필 텍스트를 수동으로 수정
        """
        profile = request.user.profile
        serializer = ProfileTextUpdateSerializer(profile, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# 2. 회원가입 View
class UserRegistrationView(APIView):
    """
    회원가입 API View
    (누구나 접근 가능해야 함)
    """
    permission_classes = [permissions.AllowAny] # 인증 없이 접근 허용

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save() # .save()가 .create()를 호출

            return Response({"message": "회원가입이 성공적으로 완료되었습니다."}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MyTokenObtainPairView(TokenObtainPairView):
    """
    로그인 view 상속받고
    serializer_class를 MyTokenObtainPairView로 지정
    """

    serializer_class = MyTokenObtainPairSerializer

# 2. AI 기반 궁합/취향 분석 리포트 제공 기능 (향후 개발 예정)
@api_view(['POST'])
def generate_compatibility_report(request: Request) -> JsonResponse:
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
def generate_conversation_starter(request: Request) -> JsonResponse:
    """
    두 사용자의 정보를 바탕으로 대화를 시작할 질문을 생성합니다. (구현 예정)
    """
    # TODO: 아래 로직을 실제로 구현해야 합니다.
    # 1. 두 사용자의 정보(user1, user2)를 request.data에서 가져옵니다.
    # 2. 두 사용자의 취미, MBTI, (선택적으로) 사주 정보를 조합하여 AI 프롬프트를 구성합니다.
    # 3. OpenAI API를 호출하여 질문을 생성하고 반환합니다.
    pass # 아직 기능이 구현되지 않았으므로 비워둡니다.


# 4. 사주 정보 조회 API (독립적인 유틸리티 함수)
@api_view(['POST'])
def get_saju_api(request: Request) -> JsonResponse:
    """
    사용자의 생년월일시분 정보를 JSON으로 받아 사주팔자를 계산하고 반환합니다.
    """
    try:
        data = request.data
        year = int(data['year'])
        month = int(data['month'])
        day = int(data['day'])
        hour = int(data['hour'])
        minute = int(data['minute'])

    except (KeyError, ValueError):
        return JsonResponse({"error": "필수 정보(year, month, day, hour, minute)가 누락되었거나, 데이터 형식이 올바르지 않습니다."}, status=status.HTTP_400_BAD_REQUEST)

    saju_data = calculate_saju(year, month, day, hour, minute)

    if "error" in saju_data:
        return JsonResponse(saju_data, status=status.HTTP_400_BAD_REQUEST)

    return JsonResponse(saju_data, status=status.HTTP_200_OK)

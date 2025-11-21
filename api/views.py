import openai
import json
from django.conf import settings
# from django.http import JsonResponse

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework_simplejwt.views import TokenObtainPairView

from .saju_calculator import calculate_saju
from .models import Profile, ProfileImage
from .serializers import (
    ProfileSerializer,
    ProfileTextUpdateSerializer,
    UserRegistrationSerializer,
    MyTokenObtainPairSerializer
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
            # 1. 텍스트 데이터 저장
            profile.nickname = data['nickname']
            profile.gender = data['gender']
            profile.year = int(data['year'])
            profile.month = int(data['month'])
            profile.day = int(data['day'])

            # '시간 모름' 처리
            birth_time_unknown = data.get('birth_time_unknown')
            if birth_time_unknown == 'true' or birth_time_unknown is True:
                profile.birth_time_unknown = True
                profile.hour = None # 시간 모름이면 null
                profile.minute = None
            else:
                profile.birth_time_unknown = False
                profile.hour = int(data.get('hour', 0))
                profile.minute = int(data.get('minute', 0))

            # 선택 정보들 (없으면 None)
            profile.job = data['job']
            profile.mbti = data.get('mbti')
            profile.location_city = data.get('location_city')
            profile.location_district = data.get('location_district')

            # hobbies 처리
            hobbies_raw = data.get('hobbies')
            if hobbies_raw:
                if isinstance(hobbies_raw, str):
                    try:
                        profile.hobbies = json.loads(hobbies_raw)
                    except json.JSONDecodeError:
                        # JSON 변환 실패 시, 그냥 문자열 하나를 리스트로 저장하거나 에러 처리
                        profile.hobbies = [hobbies_raw]
                elif isinstance(hobbies_raw, list):
                    profile.hobbies = hobbies_raw

            # 데이터 유효성 검사
            if profile.hobbies and len(profile.hobbies) < 3:
                return Response({'error': '관심사는 최소 3개 이상 선택해야 합니다.'}, status=status.HTTP_400_BAD_REQUEST)

            # 이미지 파일 저장 (최대 6개)
            # React Native에서 이미지 보낼 시, 키 이름을 'images'로 통일해서 여러 개 보내야 됨
            if 'images' in request.FILES:
                images = request.FILES.getlist('images')

                if len(images) < 2:
                    return Response({'error': '프로필 사진은 최소 2장 이상 등록해야 합니다.'}, status=status.HTTP_400_BAD_REQUEST)

                if len(images) > 6:
                    return Response({'error': '프로필 사진은 최대 6장까지만 등록 가능합니다.'}, status=status.HTTP_400_BAD_REQUEST)

                # 기존 사진 삭제하고 새로 올릴지, 추가할지는 정책 결정 필요함
                # 여기서는 모두 지우고 새로 업로드 방식으로 구현 (덮어쓰기 방식)
                profile.images.all().delete()

                for img in images:
                    ProfileImage.objects.create(profile=profile, image=img)
            else:
                # 이미지가 하나도 안 왔을 때 예외 처리 (필수 정보이므로)
                return Response({'error': '프로필 사진은 필수입니다.'}, status=status.HTTP_400_BAD_REQUEST)

        except (ValueError, TypeError):
            return Response({"error": "필수 정보가 누락되었거나, 데이터 형식이 올바르지 않습니다."}, status=status.HTTP_400_BAD_REQUEST)

        # 3. 사주 계산
        calc_hour = profile.hour if profile.hour is not None else 0
        calc_minute = profile.minute if profile.minute is not None else 0


        saju_data = calculate_saju(profile.year, profile.month, profile.day, calc_hour, calc_minute)
        if "error" in saju_data:
            return Response(saju_data, status=status.HTTP_400_BAD_REQUEST)

        my_saju_pillar = saju_data.get('day_pillar')

        # AI 프롬프트 동적 구성
        prompt_lines = [
            "아래 사용자 정보를 바탕으로, 데이팅 앱 프로필 자기소개를 200자 내외로 작성해.",
            "가장 중요한 요구사항: '타고난 사주 성향(일주)'에 담긴 기운(예: 불, 물, 나무, 쇠, 흙 등)이나 특징을 비유적으로 표현해서 반드시 문장에 포함시켜 줘.",
            "(예시: '정유일주답게 촛불처럼 주변을 밝히는...', '바위처럼 듬직한...', '흐르는 물처럼 유연한...')",
            "",
            f"- 닉네임: {profile.nickname}",
            f"- 성별: {profile.gender}",
            f"- 지역: {profile.location_city} {profile.location_district}",
            f"- 타고난 사주 성향 (일주): {my_saju_pillar}"
        ]
        if profile.job:
            prompt_lines.append(f"-직업: {profile.job}")
        if profile.hobbies:
            prompt_lines.append(f"- 관심사: {', '.join(profile.hobbies)}")
        if profile.mbti:
            prompt_lines.append(f"- MBTI: {profile.mbti}")
        prompt_lines.extend(["", "- 톤앤매너: 친근하고 긍정적인 느낌, 약간의 유머와 센스 포함"])
        prompt = "\n".join(prompt_lines)

        try:
            # OpenAI API 호출
            response = openai.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": "You are a dating profile expert"},
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
# @api_view(['POST'])
# def generate_compatibility_report(request: Request) -> JsonResponse:
#     """
#     두 사용자의 전체 정보를 받아 AI가 관계 분석 리포트를 생성합니다. (구현 예정)
#     """
    # TODO: 아래 로직을 실제로 구현해야 합니다.
    # 1. 두 사용자의 전체 정보(user1, user2)를 request.data에서 가져옵니다.
    #    각 사용자 정보에는 생년월일시분, 취미, MBTI 등이 모두 포함되어야 합니다.
    # 2. 각 사용자의 생년월일시분 정보로 calculate_saju()를 각각 호출하여 사주 데이터를 얻습니다.
    # 3. 두 사용자의 사주 데이터, 취미, MBTI를 모두 종합하여 AI 프롬프트를 구성합니다.
    # 4. OpenAI API를 호출하여 리포트를 생성하고 반환합니다.
    pass # 아직 기능이 구현되지 않았으므로 비워둡니다.


# 3. AI 기반 대화 어시스턴트 기능 (향후 개발 예정)
# @api_view(['POST'])
# def generate_conversation_starter(request: Request) -> JsonResponse:
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
def get_saju_api(request: Request) -> Response:
    """
    사용자의 생년월일시분 정보를 받아 사주팔자를 계산하고 반환합니다.
    """
    data = request.data
    try:
        year = int(data['year'])
        month = int(data['month'])
        day = int(data['day'])

        # '시간 모름' 로직
        unknown_val = data.get('birth_time_unknown')

        if unknown_val == 'true' or unknown_val is True:
            # 시간을 모르면 00시 00분으로 설정
            hour = 0
            minute = 0
        else:
            hour = int(data.get('hour', 0))
            minute = int(data.get('minute', 0))

    except (KeyError, ValueError, TypeError):
        return Response({"error": "필수 정보가 누락되었거나, 데이터 형식이 올바르지 않습니다."}, status=status.HTTP_400_BAD_REQUEST)

    # 사주 계산
    saju_data = calculate_saju(year, month, day, hour, minute)

    if "error" in saju_data:
        return Response(saju_data, status=status.HTTP_400_BAD_REQUEST)

    return Response(saju_data, status=status.HTTP_200_OK)

# TODO:
# 추가 수정 요망(졸려뒤지겠음)
# profiles/views.py

import openai
import json
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.decorators import api_view
from rest_framework.request import Request

from .models import UserProfile, ProfileImage
from profiles.serializers import (
    ProfileSerializer,
    ProfileTextUpdateSerializer,
    UserRegistrationSerializer,
    MyTokenObtainPairSerializer
)

from api.saju_calculator import calculate_saju

# settings.py에서 API 키를 불러옵니다.
openai.api_key = settings.OPENAI_API_KEY

# 1. 회원가입 View
class UserRegistrationView(APIView):
    """
    [POST] 회원가입 API
    (누구나 접근 가능해야 함)
    """
    permission_classes = [permissions.AllowAny] # 인증 없이 접근 허용

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save() # .save()가 .create()를 호출
            return Response({
                "message": "회원가입이 성공적으로 완료되었습니다."},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# 2. 로그인 View
class MyTokenObtainPairView(TokenObtainPairView):
    """
    [POST] 로그인 API
    SimpleJWT의 기본 뷰를 상속받아 시리얼라이저를 연결
    """
    serializer_class = MyTokenObtainPairSerializer

# 1. 프로필 관리 View (조회, AI 프로필 생성, 수동 수정)
class ProfileView(APIView): # (조회, AI 생성, 수동 수정)
    """
    로그인한 사용자의 프로필을 다루는 View
    - GET: 내 프로필 정보 조회
    - POST: 내 정보로 AI 프로필 생성
    - PATCH: 사용자가 AI 프로필 텍스트 수정
    """
    permission_classes = [permissions.IsAuthenticated] # 로그인 필수

    def get(self, request):
        """
        [GET] 내 프로필 조회
        """
        try:
            profile = request.user.profile
            serializer = ProfileSerializer(profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except UserProfile.DoesNotExist:
            return Response(
                {'error': '프로필이 존재하지 않습니다.'},
                status=status.HTTP_404_NOT_FOUND
            )

    def post(self, request):
        """
        [POST] 정보 입력 + 사진 업로드 -> AI 소개글 생성
        """
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        data = request.data

        try:
            # 1. 텍스트 데이터 저장
            profile.nickname = data.get('nickname')
            profile.gender = data.get('gender')
            profile.year = int(data.get('year'))
            profile.month = int(data.get('month'))
            profile.day = int(data.get('day'))

            # '시간 모름' 처리
            unknown_val = data.get('birth_time_unknown')
            if unknown_val == 'true' or unknown_val is True:
                profile.birth_time_unknown = True
                profile.hour = None
                profile.minute = None
            else:
                profile.birth_time_unknown = False
                h_val = data.get('hour')
                m_val = data.get('minute')
                # 값이 있으면 int 변환, 없으면 0
                profile.hour = int(h_val) if h_val and str(h_val).strip() else 0
                profile.minute = int(m_val) if m_val and str(m_val).strip() else 0

            # 선택 정보들 (없으면 None)
            profile.job = data.get('job')
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
                return Response(
                    {'error': '프로필 사진은 필수입니다.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            profile.save()

        except (ValueError) as e:
            return Response(
                {"error": "필수 정보가 누락됨."},
                status=status.HTTP_400_BAD_REQUEST
            )
        except (TypeError) as e:
            return Response(
                {"error": "데이터 형식이 올바르지 않습니다."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 사주 계산
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
            h_str = ', '.join(profile.hobbies) if isinstance(profile.hobbies, list) else str(profile.hobbies)
            prompt_lines.append(f"-관심사: {h_str}")
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
            profile.profile_text = response.choices[0].message.content.strip().strip('"')
            profile.save()

            serializer = ProfileSerializer(profile)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'error': f'AI 프로필 생성에 실패했습니다: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def patch(self, request):
        """
        [PATCH] AI가 쓴 글 수동 수정
        """
        try:
            profile = request.user.profile
        except UserProfile.DoesNotExist:
            return Response({'error': '프로필이 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ProfileTextUpdateSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# 4. 사주 정보 조회 API (독립적인 유틸리티 함수)
@api_view(['POST'])
def get_saju_api(request: Request) -> Response:
    """
    사용자의 생년월일시분 정보를 받아 사주팔자를 계산하고 반환합니다.
    """
    data = request.data
    print(f"\n📢 [DEBUG] 수신된 데이터: {data}")

    try:
        year = int(data['year'])
        month = int(data['month'])
        day = int(data['day'])

        # 1. '시간 모름' 로직 확인
        unknown_val = data.get('birth_time_unknown')

        # 2. hour/minute 값 안전하게 가져오기
        raw_hour = data.get('hour')
        raw_minute = data.get('minute')

        # 3. '시간 모름'이거나 값이 None(null)이면 0으로 설정
        if (unknown_val == 'true' or unknown_val is True) or (raw_hour is None):
            hour = 0
            minute = 0
        else:
            hour = int(raw_hour)
            minute = int(raw_minute)

    except Exception as e:
        print(f"[ERROR] 데이터 처리 중 오류 발생: {e}")
        print(f"   - 입력된 year 타입: {type(data.get('year'))}")

        return Response(
            {"error": f"필수 정보가 누락되었거나 형식이 잘못되었습니다. (서버 로그 확인 필요) 상세: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # 사주 계산
    saju_data = calculate_saju(year, month, day, hour, minute)

    if "error" in saju_data:
        return Response(saju_data, status=status.HTTP_400_BAD_REQUEST)

    return Response(saju_data, status=status.HTTP_200_OK)
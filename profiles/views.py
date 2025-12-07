# profiles/views.py
import json
from datetime import date, timedelta

import openai
from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from api.geo_utils import get_lat_lon
from api.saju_calculator import calculate_saju
from .models import ProfileImage, UserProfile, UserReport
from .serializers import (
    MyTokenObtainPairSerializer,
    ProfileSerializer,
    ProfileTextUpdateSerializer,
    UserRegistrationSerializer,
    UserReportSerializer
)
from chat.models import ChatRoom, Message

User = get_user_model()
openai.api_key = settings.OPENAI_API_KEY


class UserRegistrationView(APIView):
    """
    [POST] 회원가입 API
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "회원가입이 정상적으로 완료되었습니다."},
                status=status.HTTP_201_CREATED,
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class MyTokenObtainPairView(TokenObtainPairView):
    """
    [POST] 로그인 API (JWT 발급)
    """
    serializer_class = MyTokenObtainPairSerializer


class ProfileView(APIView):
    """
    프로필 조회 / 저장(이미지+AI 소개글 생성) / 소개글 수정
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            profile = request.user.profile
        except UserProfile.DoesNotExist:
            return Response(
                {"error": "프로필이 존재하지 않습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = ProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        data = request.data

        try:
            profile.nickname = data.get("nickname")
            profile.gender = data.get("gender")
            try:
                profile.year = int(data.get("year"))
                profile.month = int(data.get("month"))
                profile.day = int(data.get("day"))
            except (TypeError, ValueError):
                return Response(
                    {"error": "생년월일(year, month, day)은 필수이며 숫자여야 합니다."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            unknown_val = data.get("birth_time_unknown")
            if unknown_val == "true" or unknown_val is True:
                profile.birth_time_unknown = True
                profile.hour = None
                profile.minute = None
            else:
                profile.birth_time_unknown = False
                h_val = data.get("hour")
                m_val = data.get("minute")
                profile.hour = int(h_val) if h_val and str(h_val).strip() else 0
                profile.minute = int(m_val) if m_val and str(m_val).strip() else 0

            profile.job = data.get("job")
            profile.mbti = data.get("mbti")
            profile.location_city = data.get("location_city")
            profile.location_district = data.get("location_district")

            # 도시와 구 정보가 모두 있을 때만 실행
            if profile.location_city and profile.location_district:
                lat, lon = get_lat_lon(profile.location_city, profile.location_district)

                # API가 성공적으로 좌표를 가져왔다면 저장
                if lat is not None and lon is not None:
                    profile.latitude = lat
                    profile.longitude = lon
                else:
                    print(f"좌표 변환 실패: {profile.location_city} {profile.location_district}")


            hobbies_raw = data.get("hobbies")
            if hobbies_raw:
                if isinstance(hobbies_raw, str):
                    try:
                        hobbies_raw = hobbies_raw.replace("\x08", "").strip()
                        profile.hobbies = json.loads(hobbies_raw)
                    except json.JSONDecodeError:
                        profile.hobbies = [hobbies_raw]
                elif isinstance(hobbies_raw, list):
                    profile.hobbies = hobbies_raw

            if profile.hobbies and len(profile.hobbies) < 3:
                return Response(
                    {"error": "관심사는 최소 3개 이상 선택해야 합니다."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if "images" in request.FILES:
                images = request.FILES.getlist("images")

                if len(images) < 2:
                    return Response(
                        {"error": "프로필 사진은 최소 2장 이상 등록해야 합니다."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                if len(images) > 6:
                    return Response(
                        {"error": "프로필 사진은 최대 6장까지 등록 가능합니다."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                profile.images.all().delete()
                for img in images:
                    ProfileImage.objects.create(profile=profile, image=img)
            else:
                return Response(
                    {"error": "프로필 사진은 필수입니다."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            profile.save()

        except (ValueError, TypeError):
            return Response(
                {
                    "error": "필수 정보가 누락되었거나 입력 형식이 올바르지 않습니다."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        calc_hour = profile.hour if profile.hour is not None else 0
        calc_minute = profile.minute if profile.minute is not None else 0

        saju_data = calculate_saju(
            profile.year, profile.month, profile.day, calc_hour, calc_minute
        )
        if "error" in saju_data:
            return Response(
                saju_data,
                status=status.HTTP_400_BAD_REQUEST
            )

        my_saju_pillar = saju_data.get("day_pillar")

        prompt_lines = [
            "아래 사용자의 정보를 바탕으로, 친근한 톤으로 소개글을 200자 내외로 작성해줘.",
            "중요 요구사항: '태어난 날의 기운(일주)'을 밝은 기운이나 비유로 표현해 문장에 포함해줘.",
            "",
            f"- 닉네임: {profile.nickname}",
            f"- 성별: {profile.gender}",
            f"- 지역: {profile.location_city} {profile.location_district}",
            f"- 태어난 날의 기운(일주): {my_saju_pillar}",
        ]
        if profile.job:
            prompt_lines.append(f"- 직업: {profile.job}")
        if profile.hobbies:
            h_str = (
                ", ".join(profile.hobbies)
                if isinstance(profile.hobbies, list)
                else str(profile.hobbies)
            )
            prompt_lines.append(f"- 관심사: {h_str}")
        if profile.mbti:
            prompt_lines.append(f"- MBTI: {profile.mbti}")
        prompt_lines.extend(
            ["", "- 어조: 친근하고 긍정적인 느낌, 가벼운 유머 허용"]
        )
        prompt = "\n".join(prompt_lines)

        try:
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a dating profile expert"},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.8,
                max_tokens=300,
            )
            profile.profile_text = response.choices[0].message.content.strip().strip(
                '"'
            )
            profile.save()

            serializer = ProfileSerializer(profile)
            return Response(
                {"message": "프로필 생성이 완료되었습니다.",
                 "data": serializer.data},
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return Response(
                {"error": f"AI 소개글 생성에 실패했습니다: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def patch(self, request):
        """
        [PATCH] AI가 만든 소개글 및 프로필DB 수정
        """

        try:
            profile = request.user.profile
        except UserProfile.DoesNotExist:
            return Response(
                {"error": "프로필이 없습니다."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ProfileTextUpdateSerializer(
            profile, data=request.data, partial=True
        )
        if serializer.is_valid():
            new_city = request.data.get("location_city")
            new_district = request.data.get("location_district")

            # 요청에 지역 정보가 하나라도 포함되어 있다면?
            if new_city is not None or new_district is not None:
                # 변경할 값을 request.data에서 가져오고
                # 변경 안 한 값은 기존 DB에 있는 값을 그대로 사용
                # (빈 문자열 올 때, .strip()으로 공백 처리)
                if new_city is not None:
                    city_to_search = new_city.strip()
                else:
                    city_to_search = profile.location_city

                if new_district is not None:
                    dist_to_search = new_district.strip()
                else:
                    dist_to_search = profile.location_district

                # 도시와 구 정보가 둘 다 유효할 때만 API 호출
                if city_to_search and dist_to_search:
                    lat, lon = get_lat_lon(city_to_search, dist_to_search)

                    # 좌표 성공적으로 가져오면 인스턴스에 직접 주입
                    if lat is not None and lon is not None:
                        serializer.instance.latitude = lat
                        serializer.instance.longitude = lon

                        serializer.instance.location_city = city_to_search
                        serializer.instance.location_district = dist_to_search

            serializer.save()
            return Response(
                {
                    "message" : "프로필이 성공적으로 수정되었습니다.",
                    "data": serializer.data
                },
                status=status.HTTP_200_OK
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

class UserStatusCheckView(APIView):
    """
    [GET] /api/users/status/
    현재 로그인한 유저의 프로필 존재 여부 확인
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # 1. 프로필 객체 가져오기 시도
        try:
            profile = user.profile

            # 2. profile_text 값 있는지 확인 (None이 아니고, 빈 문자열도 아니어야 함)
            if profile.profile_text and profile.profile_text.strip():
                return Response(
                    {"has_profile": True},
                    status=status.HTTP_200_OK
                )
            else:
                # 프로필 껍데기는 있는데 내용이 비어있음
                return Response(
                    {"has_profile": False},
                    status=status.HTTP_200_OK
                )
        except Exception:
            # 프로필 객체 자체가 아예 없음
            return Response(
                {"has_profile": False},
                status=status.HTTP_200_OK
            )

class ProfileRegenerateView(APIView):
    """
    [POST] 프로필 AI 소개글 재생성 (7일 쿨다운)
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            profile = request.user.profile
        except UserProfile.DoesNotExist:
            return Response(
                {"error": "프로필이 없습니다. 먼저 프로필을 작성해주세요."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # 7일 쿨다운 체크
        now = timezone.now()
        if profile.ai_generated_at:
            cooldown_until = profile.ai_generated_at + timedelta(days=7)
            if now < cooldown_until:
                return Response(
                    {
                        "error": "AI 소개글은 7일에 한 번만 재생성할 수 있습니다.",
                        "next_regen_at": cooldown_until.isoformat(),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # 필수 정보 검증 (프롬프트 품질 보호)
        required_fields = {
            "nickname": profile.nickname,
            "gender": profile.gender,
            "location_city": profile.location_city,
            "location_district": profile.location_district,
            "year": profile.year,
            "month": profile.month,
            "day": profile.day,
        }
        missing = [k for k, v in required_fields.items() if not v]
        if missing:
            return Response(
                {"error": f"AI 소개글 재생성을 위해 필요한 정보가 없습니다: {', '.join(missing)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        calc_hour = profile.hour if profile.hour is not None else 0
        calc_minute = profile.minute if profile.minute is not None else 0
        saju_data = calculate_saju(
            profile.year, profile.month, profile.day, calc_hour, calc_minute
        )
        if "error" in saju_data:
            return Response(
                saju_data,
                status=status.HTTP_400_BAD_REQUEST
            )

        my_saju_pillar = saju_data.get("day_pillar")

        prompt_lines = [
            "아래 사용자의 정보를 바탕으로, 친근한 톤으로 소개글을 200자 내외로 작성해줘.",
            "중요 요구사항: '태어난 날의 기운(일주)'을 밝은 기운이나 비유로 표현해 문장에 포함해줘.",
            "",
            f"- 닉네임: {profile.nickname}",
            f"- 성별: {profile.gender}",
            f"- 지역: {profile.location_city} {profile.location_district}",
            f"- 태어난 날의 기운(일주): {my_saju_pillar}",
        ]
        if profile.job:
            prompt_lines.append(f"- 직업: {profile.job}")
        if profile.hobbies:
            h_str = (
                ", ".join(profile.hobbies)
                if isinstance(profile.hobbies, list)
                else str(profile.hobbies)
            )
            prompt_lines.append(f"- 관심사: {h_str}")
        if profile.mbti:
            prompt_lines.append(f"- MBTI: {profile.mbti}")
        prompt_lines.extend(
            ["", "- 어조: 친근하고 긍정적인 느낌, 가벼운 유머 허용"]
        )
        prompt = "\n".join(prompt_lines)

        try:
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a dating profile expert"},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.8,
                max_tokens=300,
            )
            profile.profile_text = response.choices[0].message.content.strip().strip(
                '"'
            )
            profile.ai_generated_at = now
            profile.save(update_fields=["profile_text", "ai_generated_at"])

            serializer = ProfileSerializer(profile)
            return Response(
                {
                    "message": "AI 소개글이 재생성되었습니다.",
                    "data": serializer.data,
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"error": f"AI 소개글 생성에 실패했습니다: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class UserProfileDetailView(APIView):
    """
    다른 사용자의 프로필 조회 (user_id 기준)
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request, user_id):
        profile = get_object_or_404(UserProfile, user__id=user_id)
        serializer = ProfileSerializer(profile)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


@api_view(["POST"])
def get_saju_api(request: Request) -> Response:
    """
    사용자의 생년월일/시간을 받아 사주 데이터를 계산해 반환
    """

    data = request.data
    try:
        year = int(data.get("year"))
        month = int(data.get("month"))
        day = int(data.get("day"))

        unknown_val = data.get("birth_time_unknown")
        raw_hour = data.get("hour")
        raw_minute = data.get("minute")

        if (unknown_val == "true" or unknown_val is True) or (raw_hour is None):
            hour = 0
            minute = 0
        else:
            hour = int(raw_hour)
            minute = int(raw_minute)

    except Exception as e:
        return Response(
            {
                "error": f"필수 정보가 누락되었거나 형식이 잘못되었습니다. 상세: {str(e)}"
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    saju_data = calculate_saju(year, month, day, hour, minute)

    if "error" in saju_data:
        return Response(
            saju_data,
            status=status.HTTP_400_BAD_REQUEST
        )

    return Response(
        saju_data,
        status=status.HTTP_200_OK
    )


class MatchSummaryView(APIView):
    """
    두 프로필(나 + 상대)을 비교해 매칭 한 줄 평을 생성
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, other_user_id):
        me = request.user
        try:
            other = User.objects.get(id=other_user_id)
        except User.DoesNotExist:
            return Response(
                {"error": "상대 사용자를 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            my_profile = me.profile
        except UserProfile.DoesNotExist:
            return Response(
                {"error": "내 프로필이 없습니다. 프로필을 먼저 작성해주세요."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            other_profile = other.profile
        except UserProfile.DoesNotExist:
            return Response(
                {"error": "상대 프로필이 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        def saju_or_none(p):
            try:
                y, m, d = int(p.year), int(p.month), int(p.day)
            except (TypeError, ValueError):
                return None
            hour = 0 if p.birth_time_unknown else int(p.hour or 0)
            minute = 0 if p.birth_time_unknown else int(p.minute or 0)
            data = calculate_saju(y, m, d, hour, minute)
            return data if "error" not in data else None

        def hobbies_str(p):
            if isinstance(p.hobbies, list):
                return ", ".join(p.hobbies)
            if isinstance(p.hobbies, str):
                return p.hobbies
            return None

        my_saju = saju_or_none(my_profile)
        other_saju = saju_or_none(other_profile)

        my_age = my_profile.age
        other_age = other_profile.age

        my_lines = [
            f"닉네임: {my_profile.nickname or me.username}",
            f"성별: {my_profile.gender or '미기재'}",
        ]
        if my_age is not None:
            my_lines.append(f"나이: {my_age}세")
        if my_profile.job:
            my_lines.append(f"직업: {my_profile.job}")
        if my_profile.mbti:
            my_lines.append(f"MBTI: {my_profile.mbti}")
        if my_profile.location_city or my_profile.location_district:
            my_lines.append(
                f"지역: {(my_profile.location_city or '').strip()} {(my_profile.location_district or '').strip()}".strip()
            )
        h = hobbies_str(my_profile)
        if h:
            my_lines.append(f"취미: {h}")
        if my_saju and my_saju.get("day_pillar"):
            my_lines.append(f"일주: {my_saju.get('day_pillar')}")

        other_lines = [
            f"닉네임: {other_profile.nickname or other.username}",
            f"성별: {other_profile.gender or '미기재'}",
        ]
        if other_age is not None:
            other_lines.append(f"나이: {other_age}세")
        if other_profile.job:
            other_lines.append(f"직업: {other_profile.job}")
        if other_profile.mbti:
            other_lines.append(f"MBTI: {other_profile.mbti}")
        if other_profile.location_city or other_profile.location_district:
            other_lines.append(
                f"지역: {(other_profile.location_city or '').strip()} {(other_profile.location_district or '').strip()}".strip()
            )
        oh = hobbies_str(other_profile)
        if oh:
            other_lines.append(f"취미: {oh}")
        if other_saju and other_saju.get("day_pillar"):
            other_lines.append(f"일주: {other_saju.get('day_pillar')}")

        prompt = (
            "주어 규칙: '당신'은 나, '상대'는 상대. 이 규칙을 모든 문장에 적용해."
            "주어 규칙의 예: 당신은 창의적이고, 상대는 대화를 즐기는 스타일이에요."
            "너는 한국어로 매칭 한 줄 평을 쓰는 카피라이터이자 사주 분석가야. "
            "두 사람의 성향과 프로필을 비교해 2~3문장, 220자 이내로 간결하게 써줘. "
            "사주는 일주/출생연도 단서로 가볍게 녹여줘. "
            "긍정적이고 따뜻한 톤, 과장/공격/훈수 금지. 이모지는 1개 이하, 선택적으로만 사용. "
            "사주를 모르는 사람도 이해할 수 있도록 비유를 곁들여줘. "
            "프로필에서 둘 다 적힌 정보만 비교에 활용하고, 비교 표현은 일관성 있게. "
            "자연스러운 구어체로, 소개팅 앱에서 상대 프로필에 노출될 문구이므로 "
            
            "\n\n[나]\n- "
            + "\n- ".join(my_lines)
            + "\n\n[상대]\n- "
            + "\n- ".join(other_lines)
        )

        try:
            completion = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You write concise Korean dating match blurbs that compare two people.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.8,
                max_tokens=220,
            )
            content = completion.choices[0].message.content.strip().strip('"')
        except Exception as e:
            return Response(
                {"error": f"매칭 한 줄 평 생성에 실패했습니다: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {"summary": content},
            status=status.HTTP_200_OK
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def report_profile_user(request, target_id):
    """
    [POST] 특정 사용자 신고하기 (프로필)
    """
    reporter = request.user

    # 1. 신고 대상 확인
    try:
        target_user = User.objects.get(id=target_id)
    except User.DoesNotExist:
        return Response({"error": "신고할 사용자를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

    # 2. 본인 신고 방지
    if reporter.id == target_user.id:
        return Response({"error": "자기 자신을 신고할 수 없습니다."}, status=status.HTTP_400_BAD_REQUEST)

    # 3. 데이터 검증 및 저장
    serializer = UserReportSerializer(data=request.data)
    if serializer.is_valid():
        UserReport.objects.create(
            reporter=reporter,
            reported_user=target_user,
            reason=serializer.validated_data['reason'],
            description="(프로필 화면에서의 신고)",
            source='PROFILE'  # 프로필에서 신고했음을 명시
        )
        return Response({"message": "신고가 정상적으로 접수되었습니다. 관리자 검토 후 처리됩니다."}, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def report_chat_user(request, target_id):
    """
    [POST] 채팅방에서 사용자 신고하기
    - 채팅방 이름(room_name)을 통해 상대방을 자동 식별
    - 해당 채팅방의 최근 대화 내역(20개)을 자동으로 첨부하여 저장
    """
    reporter = request.user

    # 1. 채팅방 및 상대방 식별
    try:
        target_user = User.objects.get(id=target_id)
    except User.DoesNotExist:
        return Response(
            {"error": "신고할 대상을 찾을 수 없습니다."},
            status=status.HTTP_404_NOT_FOUND
        )

    if reporter.id == target_user.id:
        return Response(
            {"error": "자기 자신을 신고할 수 없습니다."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # 2. 채팅방 찾기
    room = ChatRoom.objects.filter(participants=reporter).filter(participants=target_user).first()

    # 3. 채팅 로그 수집
    chat_log = ""
    try:
        # 최근 메시지 20개를 시간 역순으로 가져와서 다시 시간순 정렬
        recent_messages = Message.objects.filter(room=room).order_by('-timestamp')[:20]
        recent_messages = reversed(recent_messages)

        # 로그 문자열 생성
        log_lines = []
        for msg in recent_messages:
            sender_name = msg.sender.username
            time_str = msg.timestamp.strftime("%Y-%m-%d %H:%M")
            log_lines.append(f"[{time_str}] {sender_name}: {msg.content}")

        if log_lines:
            chat_log = "\n".join(log_lines)
        else:
            chat_log = "(대화 내역 없음)"

    except:
        # 방이 없어도 신고는 가능하지만 로그 없음을 명시함
        chat_log = "(채팅방이 존재하지 않거나 대화 내역이 없습니다."

    # 4. 데이터 검증 및 저장
    serializer = UserReportSerializer(data=request.data)
    if serializer.is_valid():
        final_description = f"=== [시스템 자동 첨부: 최근 대화 로그] ===\n{chat_log}"

        UserReport.objects.create(
            reporter=reporter,
            reported_user=target_user,
            reason=serializer.validated_data['reason'],
            description=final_description,
            source='CHAT'
        )
        return Response(
            {"message": "신고가 접수되었습니다. 대화 내역이 함께 전송되었습니다."},
            status=status.HTTP_201_CREATED
        )
    return Response(serializer.errors,
        status = status.HTTP_400_BAD_REQUEST)

# class FCMTokenregisterView(APIView):
#     """
#     [POST] /api/users/fcm/register/
#     FCM 토큰을 DB에 업데이트
#     """
#     permissions_classes = [permissions.IsAuthenticated]
#
#     def post(self, request):
#         token = request.data.get("fcm_token")
#         if not token:
#             return Response(
#                 {"error": "토큰이 없습니다."},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#
#         profile = request.user.profile
#         profile.fcm_token = token
#         profile.save()
#
#         return Response(
#             {"message": "FCM 토큰이 등록되었습니다."},
#             status=status.HTTP_200_OK
#         )
import openai
from django.conf import settings
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework import status

# 사주 계산 로직을 불러옵니다. 이 함수가 모든 사주 관련 계산을 전담합니다.
from .saju_calculator import calculate_saju

# settings.py에서 API 키를 불러옵니다.
openai.api_key = settings.OPENAI_API_KEY


# 1. AI 기반 프로필 자동 생성 기능 (기준이 되는 핵심 함수)
@api_view(['POST'])
def generate_profile(request: Request) -> JsonResponse:
    """
    사용자의 필수 정보와 선택 정보(취미, MBTI)를 받아
    사주를 계산하고, 이를 결합하여 AI 프로필을 생성합니다.
    """
    try:
        data = request.data
        # 필수 정보 추출 및 변환
        nickname = data['nickname']
        year = int(data['year'])
        month = int(data['month'])
        day = int(data['day'])
        hour = int(data['hour'])
        minute = int(data['minute'])
        gender = data['gender']
        job = data['job']
        # 선택 정보 추출
        hobbies = data.get('hobbies')
        mbti = data.get('mbti')

        if hobbies and not isinstance(hobbies, list):
            return JsonResponse({'error': '취미(hobbies)는 반드시 리스트(배열) 형태여야 합니다.'}, status=status.HTTP_400_BAD_REQUEST)

    except (KeyError, ValueError):
        return JsonResponse({"error": "필수 정보가 누락되었거나, 데이터 형식이 올바르지 않습니다."}, status=status.HTTP_400_BAD_REQUEST)

    # 사주 계산
    saju_data = calculate_saju(year, month, day, hour, minute)
    if "error" in saju_data:
        return JsonResponse(saju_data, status=status.HTTP_400_BAD_REQUEST)

    my_saju_pillar = saju_data.get('day_pillar')

    # AI 프롬프트 동적 구성
    prompt_lines = [
        "아래 정보를 바탕으로, 데이팅 앱에서 사용할 매력적이고 진솔한 자기소개 문구를 200자 내외로 자연스럽게 작성해줘.",
        "특히 '타고난 사주 성향' 정보를 참고해서 그 사람의 성격이 은은하게 드러나도록 문장을 만들어 줘.",
        "",
        f"- 닉네임: {nickname}",
        f"- 성별: {gender}",
        f"- 직업: {job}",
        f"- 타고난 사주 성향 (일주): {my_saju_pillar}"
    ]
    if hobbies:
        prompt_lines.append(f"- 취미: {', '.join(hobbies)}")
    if mbti:
        prompt_lines.append(f"- MBTI: {mbti}")
    prompt_lines.extend(["", "- 톤앤매너: 친근하고 긍정적인 느낌, 약간의 유머와 센스 포함"])
    prompt = "\n".join(prompt_lines)

    try:
        # OpenAI API 호출
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a creative assistant who is an expert in writing appealing dating app profiles based on personality and Saju."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=300
        )
        profile_text = response.choices[0].message.content
        cleaned_profile = profile_text.strip().strip('"')
        return JsonResponse({'profile': cleaned_profile}, status=status.HTTP_201_CREATED)

    except Exception as e:
        return JsonResponse({'error': f'AI 프로필 생성에 실패했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
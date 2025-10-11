from django.shortcuts import render

# Create your views here.
import openai
import requests
from django.conf import settings
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework import status

# saju_calculator.py에서 calculate_saju 함수 풀러옴
from .saju_calculator import calculate_saju

# settings.py에서 API 키 불러오기
openai.api_key = settings.OPENAI_API_KEY

# 가상의 사주 API 호출 함수 (실제로는 이 부분을 실제 API에 맞게 수정해야 합니다)
def get_saju_data(birth_date):
    """
    사용자의 생년월일 정보를 바탕으로 가상의 사주 분석 API를 호출합니다.
    실제 프로젝트에서는 실제 사주 API 명세에 맞춰 요청 및 응답 처리를 구현해야 합니다.
    """
    try:
        # response = requests.post(settings.SAJU_API_URL, headers={'Authorization': f'Bearer {settings.SAJU_API_KEY}'}, json={'birth_date': birth_date})
        # response.raise_for_status()
        # return response.json()

        # --- 아래는 API를 찾기 전, 테스트를 위한 가상 데이터입니다 ---
        if birth_date == "1995-03-15":
            return {
                "element": "목(木)",
                "zodiac": "돼지띠",
                "daily_energy": "갑자(甲子)",
                "summary": "창의적이고 따뜻한 성품을 지녔으며, 새로운 시작을 두려워하지 않습니다. 다만 고집이 세고 충동적인 면이 있습니다."
            }
        else:
            return {
                "element": "수(水)",
                "zodiac": "쥐띠",
                "daily_energy": "임자(壬子)",
                "summary": "지혜롭고 적응력이 뛰어나며, 사람들과의 관계를 중시합니다. 신중하지만 때로는 우유부단할 수 있습니다."
            }
    except requests.exceptions.RequestException as e:
        print(f"사주 API 오류: {e}")
        return None


# 1. AI 기반 프로필 자동 생성 기능
@api_view(['POST'])
def generate_profile(request: Request) -> JsonResponse:
    """
    사용자의 최소 정보(닉네임, 직업, 취미, MBTI)를 받아 AI로 매력적인 프로필 소개글을 생성합니다.
    """
    nickname = request.data.get('nickname')
    birth_date = request.data.get('birth_date')
    user_gender = request.data.get('user_gender')
    job = request.data.get('job')
    hobbies = request.data.get('hobbies') # 예: ["영화감상", "코딩"]
    mbti = request.data.get('mbti')

    if not all([nickname, job, hobbies, mbti]):
        return JsonResponse({'error': '필수 정보가 누락되었습니다.'}, status=status.HTTP_400_BAD_REQUEST)

    # AI에게 전달할 프롬프트 (명령어) 구성
    prompt = f"""
    아래 정보를 바탕으로, 데이팅 앱에서 사용할 매력적이고 진솔한 자기소개 문구를 200자 내외로 작성해줘.
    - 닉네임: {nickname}
    - 직업: {job}
    - 취미: {', '.join(hobbies)}
    - MBTI: {mbti}
    - 톤앤매너: 친근하고 긍정적인 느낌, 약간의 유머 포함
    """

    try:
        response = openai.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": "You are a helpful assistant who is an expert in writing dating app profiles."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=250
        )
        profile_text = response.choices[0].message.content
        cleaned_profile = profile_text.strip('"').rstrip('함').strip()

        return JsonResponse({'profile': cleaned_profile}, status=status.HTTP_201_CREATED)

    except Exception as e:
        return JsonResponse({'error': f'AI 프로필 생성 실패: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# 2. AI 기반 궁합/취향 분석 리포트 제공 기능
@api_view(['POST'])
def generate_compatibility_report(request: Request) -> JsonResponse:
    """
    두 사용자의 정보(사주, 취미, MBTI 등)를 결합하여 AI가 관계 분석 리포트를 생성합니다.
    """
    user1_info = request.data.get('user1') # 예: {'birth_date': '1995-03-15', 'hobbies': ['등산', '요리'], 'mbti': 'ENFP'}
    user2_info = request.data.get('user2') # 예: {'birth_date': '1996-08-20', 'hobbies': ['음악감상', '독서'], 'mbti': 'ISTJ'}

    # 1. 각 사용자의 사주 정보 가져오기
    user1_saju = get_saju_data(user1_info['birth_date'])
    user2_saju = get_saju_data(user2_info['birth_date'])

    if not user1_saju or not user2_saju:
        return JsonResponse({'error': '사주 정보를 분석하는 데 실패했습니다.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # 2. AI에게 전달할 프롬프트 구성
    prompt = f"""
    아래는 두 사람의 사주 및 개인 성향 데이터야. 이 데이터를 종합적으로 분석해서 아래 항목에 맞춰 리포트를 작성해줘.

    [사용자 1 정보]
    - 사주 요약: {user1_saju['summary']}
    - 취미: {', '.join(user1_info['hobbies'])}
    - MBTI: {user1_info['mbti']}

    [사용자 2 정보]
    - 사주 요약: {user2_saju['summary']}
    - 취미: {', '.join(user2_info['hobbies'])}
    - MBTI: {user2_info['mbti']}

    ---

    [리포트 생성 항목]
    1. **두 사람의 적합성**: 사주와 MBTI를 기반으로 서로 어떤 점에서 잘 맞고 어떤 점에서 보완이 필요한지 분석해줘.
    2. **추천 활동 및 대화 주제**: 두 사람의 공통 및 개별 취미를 고려하여 함께하면 좋을 활동 3가지와 대화를 시작하기 좋은 주제 3가지를 제안해줘.
    3. **향후 관계 발전 가능성**: 두 사람의 성향을 종합하여 장기적인 관계로 발전할 가능성에 대해 긍정적인 관점에서 조언해줘.

    리포트는 친근하고 다정한 말투로 작성해줘.
    """

    try:
        response = openai.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": "You are a helpful assistant who is an expert in relationship counseling and Saju analysis."},
                {"role": "user", "content": prompt}
            ]
        )
        report_text = response.choices[0].message.content.strip()
        return JsonResponse({'report': report_text}, status=status.HTTP_200_OK)

    except Exception as e:
        return JsonResponse({'error': f'AI 리포트 생성 실패: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# 3. AI 기반 대화 어시스턴트 기능
@api_view(['POST'])
def generate_conversation_starter(request: Request) -> JsonResponse:
    """
    두 사용자의 대화가 단절되었을 때, AI가 맞춤형 질문을 생성하여 알림으로 제공합니다.
    (실제 알림 기능은 별도 구현 필요)
    """
    user1_info = request.data.get('user1') # 예: {'hobbies': ['등산', '요리'], 'mbti': 'ENFP'}
    user2_info = request.data.get('user2') # 예: {'hobbies': ['음악감상', '독서'], 'mbti': 'ISTJ'}

    # 1. 각 사용자의 사주 정보 가져오기 (여기서는 간단히 취미/MBTI만 활용)
    # 필요하다면 get_saju_data()를 호출하여 사주 정보도 프롬프트에 추가할 수 있습니다.

    # 2. AI에게 전달할 프롬프트 구성
    prompt = f"""
    데이팅 앱에서 매칭된 두 사람의 대화가 잠시 멈췄어. 아래 정보를 바탕으로 두 사람의 대화를 다시 자연스럽게 시작할 수 있는 재미있고 개인화된 질문을 3개만 만들어줘.

    [사용자 1 정보]
    - 취미: {', '.join(user1_info['hobbies'])}
    - MBTI: {user1_info['mbti']}

    [사용자 2 정보]
    - 취미: {', '.join(user2_info['hobbies'])}
    - MBTI: {user2_info['mbti']}

    [질문 생성 가이드]
    - 두 사람의 공통 관심사나 서로 궁금해할 만한 지점을 연결해줘.
    - 너무 사적이거나 부담스러운 질문은 피해줘.
    - 상대방이 쉽게 답할 수 있도록 열린 질문 형태로 만들어줘.
    - 예시: "두 분 다 음악을 좋아하시네요! 혹시 최근에 가장 인상 깊게 들었던 노래가 있다면 공유해주실 수 있나요?"
    """

    try:
        response = openai.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": "You are a witty and creative assistant who helps people start conversations."},
                {"role": "user", "content": prompt}
            ]
        )
        questions = response.choices[0].message.content.strip().split('\n')
        # 생성된 질문 중 하나를 랜덤으로 선택하여 알림으로 보낼 수 있습니다.
        # 여기서는 생성된 질문 목록 전체를 반환합니다.
        return JsonResponse({'questions': questions}, status=status.HTTP_200_OK)

    except Exception as e:
        return JsonResponse({'error': f'AI 질문 생성 실패: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def get_saju_api(request: Request):
    """
    사용자 정보를 받아 사주팔자를 JSON으로 반환하는 API
    """
    try:
        # 1. Postman 등에서 보낸 JSON 데이터에서 생년월일시 정보를 추출
        name = request.data.get('name')
        year = int(request.data.get('year'))
        month = int(request.data.get('month'))
        day = int(request.data.get('day'))
        hour = int(request.data.get('hour'))

        # 2. 추출한 정보를 saju_calculator.py의 calculate_saju 함수로 전달
        saju_data = calculate_saju(year, month, day, hour)

        # 3. 계산된 결과에 error가 있는지 확인(ex. 유효하지 않은 날짜)
        if "error" in saju_data:
            return JsonResponse(saju_data, status=status.HTTP_400_BAD_REQUEST)

        # 4. 성공적으로 계산된 사주 데이터를 JSON 형태로 클라이언트에게 응답
        return JsonResponse(saju_data, status=status.HTTP_200_OK)

    except (ValueError, TypeError, KeyError) as e:
        # 데이터가 잘못 들어왔을 경우의 예외 처리
        return JsonResponse({"error": "입력 데이터가 누락되었거나 형식이 올바르지 않습니다."}, status=HTTP)
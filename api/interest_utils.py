# api/interest_utils.py

# 1. 취미 키워드 -> 대분류 매핑 데이터
KEYWORD_TO_CATEGORY = {
    # 1. 운동 및 피트니스
    "골프": "운동", "농구": "운동", "러닝": "운동", "서핑": "운동",
    "스키": "운동", "스노우보드": "운동", "스킨스쿠버": "운동", "야구": "운동",
    "요가": "운동", "헬스": "운동", "자전거": "운동", "축구": "운동",
    "크로스핏": "운동", "클라이밍": "운동", "테니스": "운동",
    "프리다이빙": "운동", "필라테스": "운동",

    # 2. 여행 및 야외활동
    "낚시": "여행", "드라이브": "여행", "등산": "여행", "산책": "여행",
    "맛집 투어": "여행", "맛집": "여행", "스포츠 관람": "여행",
    "여행": "여행", "캠핑": "여행", "파인 다이닝": "여행",

    # 3. 문화 및 예술
    "게임": "문화", "공연 관람": "문화", "공연": "문화", "노래": "문화",
    "댄스": "문화", "그림": "문화", "글쓰기": "문화", "독서": "문화",
    "웹툰": "문화", "덕질": "문화", "악기": "문화", "사진": "문화",
    "전시회": "문화", "술": "문화", "애니메이션": "문화",
    "영화": "문화", "예능": "문화",

    # 4. 생활 및 자기관리
    "반려동물": "생활", "봉사활동": "생활", "인테리어": "생활",
    "자기 개발": "생활", "자기개발": "생활", "뷰티": "생활",
    "외국어 공부": "생활", "쇼핑": "생활", "자동차": "생활",
    "패션": "생활", "SNS": "생활"
}

def get_interest_score(hobbies_a, hobbies_b):
    """
    두 사용자의 취미 리스트(JSON list)를 입력받아
    취향 유사도 점수(0~100점)를 반환함

    [알고리즘]
    1. 정확히 일치하는 키워드 1개당: +10점
    2. 키워드는 달라도 대분류(카테고리)가 같으면: +3점 (카테고리 중복 합산 X)
    3. 최대 점수를 넘지 않도록 100점 만점으로 환산
    """

    # 입력값이 없거나 리스트가 아니면 0점 (방어 코드)
    if not hobbies_a or not hobbies_b:
        return 0
    if not isinstance(hobbies_a, list) or not isinstance(hobbies_b, list):
        return 0

    set_a = set(hobbies_a)
    set_b = set(hobbies_b)

    # 1. 키워드 정확 일치 개수 계산
    exact_matches = set_a.intersection(set_b)
    exact_count = len(exact_matches)

    # 2. 대분류(카테고리) 일치 여부 계싼
    # 각 사용자의 취미가 어떤 카테고리들에 속하는지 추출
    categories_a = {KEYWORD_TO_CATEGORY.get(h) for h in set_a if KEYWORD_TO_CATEGORY.get(h)}
    categories_b = {KEYWORD_TO_CATEGORY.get(h) for h in set_b if KEYWORD_TO_CATEGORY.get(h)}

    common_categories = categories_a.intersection(categories_b)
    category_count = len(common_categories)

    # 3. 원시 점수 계산
    # 예: 키워드 2개 일치(20점) + 운동 카테고리 겹침(3점) = 23점
    raw_score = (exact_count * 10) + (category_count * 3)

    # 4. 100점 만점으로 스케일링 (Normalization)
    # 기준: 취미 5개를 선택했을 때, 3개가 똑같고 카테고리도 3개 겹치면 -> 30 + 9 = 39점
    # 3~4개만 맞아도 거의 운명의 상대로 보므로, 40점 정도로 만점 기준으로 잡고 환산합니다.

    BASELINE_MAX = 40.0
    final_score = int((raw_score / BASELINE_MAX) * 100)

    # 100점 초과하면 100점으로 제한
    return max(0, min(100, final_score))
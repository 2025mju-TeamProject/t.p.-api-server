# api/interest_utils.py

import numpy as np

# 취미 키워드 → 카테고리 매핑
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

# 고정 vocabulary와 인덱스 매핑
_KEYWORDS = sorted(KEYWORD_TO_CATEGORY.keys())
_CATEGORIES = sorted(set(KEYWORD_TO_CATEGORY.values()))
_KEYWORD_TO_IDX = {k: i for i, k in enumerate(_KEYWORDS)}
_CATEGORY_TO_IDX = {c: i for i, c in enumerate(_CATEGORIES)}


def _vectorize(hobbies):
    """취미 리스트를 키워드/카테고리 벡터로 변환"""
    kw_vec = np.zeros(len(_KEYWORDS), dtype=float)
    cat_vec = np.zeros(len(_CATEGORIES), dtype=float)

    for h in hobbies:
        if h in _KEYWORD_TO_IDX:
            kw_vec[_KEYWORD_TO_IDX[h]] = 1.0
        cat = KEYWORD_TO_CATEGORY.get(h)
        if cat and cat in _CATEGORY_TO_IDX:
            cat_vec[_CATEGORY_TO_IDX[cat]] = 1.0
    return kw_vec, cat_vec


def _cosine(a, b):
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def get_interest_score(hobbies_a, hobbies_b):
    """
    취미 리스트(JSON list) 간 코사인 유사도 기반 점수(0~100) 반환

    - 키워드 벡터와 카테고리 벡터를 이어붙이고, 취미 파트 가중치 2, 카테고리 파트 가중치 1 적용
    - 입력이 없거나 벡터 노름이 0이면 0점
    """
    if not hobbies_a or not hobbies_b:
        return 0
    if not isinstance(hobbies_a, list) or not isinstance(hobbies_b, list):
        return 0

    kw_a, cat_a = _vectorize(hobbies_a)
    kw_b, cat_b = _vectorize(hobbies_b)

    # 가중치 적용
    kw_a *= 2.0
    kw_b *= 2.0

    vec_a = np.concatenate([kw_a, cat_a])
    vec_b = np.concatenate([kw_b, cat_b])

    score = _cosine(vec_a, vec_b) * 100.0
    return int(round(score))


def get_interest_debug(hobbies_a, hobbies_b):
    """
    디버깅용: 두 취미 리스트의 벡터와 코사인 유사도를 모두 반환
    """
    kw_a, cat_a = _vectorize(hobbies_a or [])
    kw_b, cat_b = _vectorize(hobbies_b or [])

    kw_a_w = kw_a * 2.0
    kw_b_w = kw_b * 2.0
    vec_a = np.concatenate([kw_a_w, cat_a])
    vec_b = np.concatenate([kw_b_w, cat_b])

    cosine = _cosine(vec_a, vec_b)

    return {
        "keywords": _KEYWORDS,
        "categories": _CATEGORIES,
        "user_a": {
            "keyword_vector": kw_a.tolist(),
            "category_vector": cat_a.tolist(),
        },
        "user_b": {
            "keyword_vector": kw_b.tolist(),
            "category_vector": cat_b.tolist(),
        },
        "weighted_cosine": cosine,
        "score_0_100": int(round(cosine * 100.0)),
    }

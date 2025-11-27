# api/geo_utils.py

import math

# --- 1. 대한민국 주요 시/군/구 위도(Lat), 경도(Lon) 데이터 ---
# (MVP 모델용: 서울, 경기 및 주요 광역시 중심)
# 실제 서비스 시에는 더 방대한 데이터나 카카오맵 API 등을 사용해야 합니다.
DISTRICT_COORDINATES = {
    # 서울
    "서울시 강남구": (37.5172, 127.0473),
    "서울시 서초구": (37.4837, 127.0324),
    "서울시 송파구": (37.5145, 127.1066),
    "서울시 마포구": (37.5665, 126.9018),
    "서울시 용산구": (37.5326, 126.9900),
    "서울시 종로구": (37.5726, 126.9796),
    "서울시 중구": (37.5636, 126.9975),
    "서울시 영등포구": (37.5264, 126.8962),
    "서울시 강서구": (37.5510, 126.8495),
    "서울시 관악구": (37.4784, 126.9516),

    # 경기 (주요 도시)
    "경기도 성남시": (37.4200, 127.1265), # 분당 등
    "경기도 수원시": (37.2636, 127.0286),
    "경기도 용인시": (37.2410, 127.1775),
    "경기도 고양시": (37.6584, 126.8320), # 일산 등
    "경기도 부천시": (37.5034, 126.7660),
    "경기도 안양시": (37.3943, 126.9568),
    "경기도 파주시": (37.7600, 126.7800),

    # 광역시/지방 (예시)
    "부산시 해운대구": (35.1631, 129.1636),
    "부산시 부산진구": (35.1630, 129.0530),
    "인천시 연수구": (37.4100, 126.6780), # 송도
    "대구시 수성구": (35.8580, 128.6300),
    "대전시 유성구": (36.3620, 127.3560),
    "강원도 강릉시": (37.7519, 128.8760),
    "제주시": (33.4996, 126.5312),
}

def get_lat_lon(city, district):
    """
    유저의 주소(시 + 구) 입력 받고 (위도, 경도) 튜플을 반환함
    데이터에 없으면 서울시청 좌표(기본값)를 반환하거나 None 처리함.(기본값 없이 None으로 처리 ㄱㄴ한지 물어보기)
    """
    if not city or not district:
        return None

    # 키 생성 (예: "서울시 강남구")
    key = f"{city} {district}"

    # 좌표 찾기
    return DISTRICT_COORDINATES.get(key)

def calculate_distance(coord1, coord2):
    """Haversine 공식을 사용하여 두 좌표(위도, 경도) 간의 거리(km) 계산"""

    if not coord1 or not coord2:
        return 9999 # 거리 계산 불가 시, 아주 먼 것으로 처리

    lat1, lon1 = coord1
    lat2, lon2 = coord2

    R = 6371 # 지구의 반지름 (km)

    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)

    a = math.sin(d_lat / 2) * math.sin(d_lat / 2) + \
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
        math.sin(d_lon / 2) * math.sin(d_lon / 2)

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return distance

def get_distance_score(distance_km):
    """
    거리에 따른 점수 반환 (선형적 로직 적용)
    - 0~20km: 10점
    - 20~30km: 9점
    - 30~50km: 8점
    - 50~100km: 7점
    - 100km 이상: 5점 (기본 점수)
    """
    if distance_km <= 20:
        return 10
    elif distance_km <= 30:
        return 9
    elif distance_km <= 50:
        return 8
    elif distance_km <= 100:
        return 7
    else:
        return 5 # 너무 멀면 5점 부여
# api/geo_utils.py

import math, requests
from django.conf import settings


def get_lat_lon(city, district):
    """
    카카오 로컬 API를 이용해 주소(시 + 구)를 위도/경도로 변환하는 함수
    Return: (latitude, longitude) 또는 (None, None)
    """

    # 1. API 키 가져오기
    rest_api_key = settings.KAKAO_API_KEY
    if not rest_api_key:
        print("Error: 카카오 API 키가 설정되지 않았습니다.")
        return None, None

    # 2. 검색할 주소 조합 (예: "서울시 강남구")
    query = f"{city} {district}"

    # 3. 카카오 API URL 및 헤더 설정
    url = "https://dapi.kakao.com/v2/local/search/address.json"
    headers = {
        "Authorization": f"KakaoAK {rest_api_key}"
    }
    params = {
        "query": query,
    }

    try:
        # 4. 요청 보내기
        response = requests.get(url, headers=headers, params=params, timeout=5)

        if response.status_code == 200:
            result = response.json()
            documents = result.get('documents')

            if documents:
                # 첫 번째 검색 결과 가져오기
                address = documents[0]

                # y: 위도, x: 경도
                latitude = float(address['y'])
                longitude = float(address['x'])

                return latitude, longitude
            else:
                print(f"주소 검색 결과가 없습니다: {query}")
                return None, None
        else:
            print(f"API 요청 실패: {response.status_code}")
            return None, None

    except Exception as e:
        print(f"좌표 변환 중 에러 발생: {str(e)}")
        return None, None

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
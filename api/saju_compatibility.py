# api/saju_compatibility.py

import os
import numpy as np
import pandas as pd
from django.conf import settings

import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.metrics import MeanSquaredError

from api.saju_calculator import calculate_saju

MODEL_DIR = os.path.join(settings.BASE_DIR, 'api', 'ml_models')
SKY_MODEL_PATH = os.path.join(MODEL_DIR, 'sky3000.h5')
EARTH_MODEL_PATH = os.path.join(MODEL_DIR, 'earth3000.h5')

# 서버 구동할 때마다 모델 로딩하면 느려짐 -> 전역 변수에 담아두고 재사용
_sky_model = None
_earth_model = None

SKY_MAP = {'갑':1, '을':2, '병':3, '정':4, '무':5, '기':6, '경':7, '신':8, '임':9, '계':10}
EARTH_MAP = {'자':1, '축':2, '인':3, '묘':4, '진':5, '사':6, '오':7, '미':8, '신':9, '유':10, '술':11, '해':12}

GAN_HAP = {1:6, 2:7, 3:8, 4:9, 5:10, 6:1, 7:2, 8:3, 9:4, 10:5} # 합 (Difference 5)
JI_HAP = [{1,2}, {3,12}, {4,11}, {5,10}, {6,9}, {7,8}]         # 육합

def load_dl_models():
    """딥러닝 모델 로드(최초 1회만 실행)"""
    global _sky_model, _earth_model

    # 모델 로드 시, 커스텀 메트릭(mse) 설정이 필요할 수 있음
    custom_objects = {'mse': MeanSquaredError()}

    # Sky 모델 로드
    if _sky_model is None:
        print("[System] Sky 모델 로드 중...")
        try:
            _sky_model = load_model(SKY_MODEL_PATH, custom_objects=custom_objects)
            print("Sky 모델 로드 성공")
        except Exception as e:
            print(f"Sky 모델 로드 실패: {e}")

    # Earth 모델 로드
    if _earth_model is None:
        print("⏳ [System] Earth 모델 로드 중...")
        try:
            _earth_model = load_model(EARTH_MODEL_PATH, custom_objects=custom_objects)
            print("Earth 모델 로드 성공")
        except Exception as e:
            print(f"Earth 모델 로드 실패: {e}")

def check_relation_score(val1, val2, typ='sky'):
    """두 글자 간의 관계 점수 계산 (0~10점)"""
    # 1. 합 체크 : 10점 (최고 궁합)
    if type == 'sky':
        # 천간합 조건: 절대값 차이가 5
        if abs(val1 - val2) == 5: return 10
    else: # earth
        # 지지육합 조거니 쌍이 리스트에 있는지 확인
        if {val1, val2} in JI_HAP: return 10

    # 2. 같은 글자(비견): 6점 (친구 같은 관계)
    if val1 == val2: return 6

    # 3. 그 외 (충 등): 4점 (기본)
    return 4

def calculate_compatibility_score(user1_profile, user2_profile):
    """[메인 로직] 두 유저의 프로필을 받아 궁합 점수(0~100) 반환"""
    # 1. 모델 로드 (메모리에 없으면 로드)
    load_dl_models()

    # 2. 사주 정보 추출 / 숫자로 변환하는 내부 합수
    def get_vectors(profile):
        # 시간 모름 처리
        h = profile.hour if profile.hour is not None else 0
        m = profile.minute if profile.minute is not None else 0

        # 사주 글자 뽑기
        saju = calculate_saju(profile.year, profile.month, profile.day, h, m)

        if "error" in saju: return None

        # 글자를 숫자로 매핑 (갑->1, 자->1)
        return {
            "ys": SKY_MAP[saju['year_pillar'][0]], "ye": EARTH_MAP[saju['year_pillar'][1]],
            "ms": SKY_MAP[saju['month_pillar'][0]], "me": EARTH_MAP[saju['month_pillar'][1]],
            "ds": SKY_MAP[saju['day_pillar'][0]], "de": EARTH_MAP[saju['day_pillar'][1]]
        }

    # 두 유저의 벡터 구하기
    u1_vec = get_vectors(user1_profile)
    u2_vec = get_vectors(user2_profile)

    # 정보 부족 시, 기본 점수 50점 반환
    if not u1_vec or not u2_vec: return 50

    # 3. 각 기둥별 관계 점수 계산 (0~10점)
    score_ys = check_relation_score(u1_vec['ys'], u2_vec['ys'], 'sky')
    score_ds = check_relation_score(u1_vec['ds'], u2_vec['ds'], 'sky')

    score_ye = check_relation_score(u1_vec['ye'], u2_vec['ye'], 'earth')
    score_me = check_relation_score(u1_vec['me'], u2_vec['me'], 'earth')
    score_de = check_relation_score(u1_vec['de'], u2_vec['de'], 'earth')

    # 가중치 공식 적용 (score = (0.6*ys) + (4.5*ds) + (1.0*ye) + (1.5*me) + (4.5*de)
    weighted_score = (0.6 * score_ys) + (4.5 * score_ds) + (1.0 * score_ye) + (1.5 * score_me) + (4.5 * score_de)

    # 5. 100점으로 환산
    final_score = int((weighted_score / 121) * 100)

    # 6. (선택) 딥러닝 모델 예측값 로그 찍어보기 (잘 로드됐는지 확인용)
    if _sky_model is not None:
        try:
            # 임시 입력값으로 예측 시도 (에러 안 나면 성공)
            sample_input = np.array([[u1_vec['ds'], u2_vec['ds']]])
            _ = _sky_model.predict(sample_input, verbose=0)
        except:
            pass

            # 점수 범위 제한 (0~100)
    return max(0, min(100, final_score))
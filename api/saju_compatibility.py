# api/saju_compatibility.py

import os
import numpy as np
import pandas as pd
from django.conf import settings

# 딥러닝 관련
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.metrics import MeanSquaredError

from api.saju_calculator import calculate_saju

MODEL_DIR = os.path.join(settings.BASE_DIR, 'api', 'ml_models')
SKY_MODEL_PATH = os.path.join(MODEL_DIR, 'sky3000.h5')
EARTH_MODEL_PATH = os.path.join(MODEL_DIR, 'earth3000.h5')

# 모델 전역 변수
_sky_model = None
_earth_model = None

SKY_MAP = {'갑': 1, '을': 2, '병': 3, '정': 4, '무': 5, '기': 6, '경': 7, '신': 8, '임': 9, '계': 10}
EARTH_MAP = {'자': 1, '축': 2, '인': 3, '묘': 4, '진': 5, '사': 6, '오': 7, '미': 8, '신': 9, '유': 10, '술': 11, '해': 12}

GAN_HAP = {1: 6, 2: 7, 3: 8, 4: 9, 5: 10, 6: 1, 7: 2, 8: 3, 9: 4, 10: 5}
JI_HAP = [{1, 2}, {3, 12}, {4, 11}, {5, 10}, {6, 9}, {7, 8}]


def load_dl_models():
    """딥러닝 모델 로드 (최초 1회만 실행)"""
    global _sky_model, _earth_model

    custom_objects = {'mse': MeanSquaredError()}

    if _sky_model is None:
        print("⏳ [System] Sky 모델 로드 중...")
        try:
            _sky_model = load_model(SKY_MODEL_PATH, custom_objects=custom_objects)
        except Exception as e:
            print(f"🚨 Sky 모델 로드 실패: {e}")

    if _earth_model is None:
        print("⏳ [System] Earth 모델 로드 중...")
        try:
            _earth_model = load_model(EARTH_MODEL_PATH, custom_objects=custom_objects)
        except Exception as e:
            print(f"🚨 Earth 모델 로드 실패: {e}")


def check_relation_score(val1, val2, typ='sky'):
    """두 글자 간의 관계 점수 계산 (0~10점)"""
    if typ == 'sky':
        if abs(val1 - val2) == 5: return 10
    else:
        if {val1, val2} in JI_HAP: return 10

    if val1 == val2: return 6
    return 4


def calculate_compatibility_score(user1_profile, user2_profile):
    """[메인 로직] 두 유저의 프로필을 받아 궁합 점수(0~100) 반환"""
    load_dl_models()

    def get_vectors(profile):
        # 1. 필수 데이터 검증
        if not profile.year or not profile.month or not profile.day:
            return None

        try:
            y = int(profile.year)
            m_ = int(profile.month)
            d = int(profile.day)
            h = int(profile.hour) if profile.hour is not None else 0
            min_ = int(profile.minute) if profile.minute is not None else 0
        except ValueError:
            return None  # 숫자가 아닌 값이 들어있으면 중단

        # 2. 사주 계산
        saju = calculate_saju(y, m_, d, h, min_)

        if "error" in saju: return None

        # 3. 매핑 (get을 사용하여 안전하게)
        return {
            "ys": SKY_MAP.get(saju['year_pillar'][0], 0), "ye": EARTH_MAP.get(saju['year_pillar'][1], 0),
            "ms": SKY_MAP.get(saju['month_pillar'][0], 0), "me": EARTH_MAP.get(saju['month_pillar'][1], 0),
            "ds": SKY_MAP.get(saju['day_pillar'][0], 0), "de": EARTH_MAP.get(saju['day_pillar'][1], 0)
        }

    # 벡터 구하기
    u1_vec = get_vectors(user1_profile)
    u2_vec = get_vectors(user2_profile)

    if not u1_vec or not u2_vec: return 50

    # 점수 계산
    score_ys = check_relation_score(u1_vec['ys'], u2_vec['ys'], 'sky')
    score_ds = check_relation_score(u1_vec['ds'], u2_vec['ds'], 'sky')
    score_ye = check_relation_score(u1_vec['ye'], u2_vec['ye'], 'earth')
    score_me = check_relation_score(u1_vec['me'], u2_vec['me'], 'earth')
    score_de = check_relation_score(u1_vec['de'], u2_vec['de'], 'earth')

    # 가중치 공식
    weighted_score = (0.6 * score_ys) + (4.5 * score_ds) + (1.0 * score_ye) + (1.5 * score_me) + (4.5 * score_de)

    final_score = int((weighted_score / 121) * 100)

    # 모델 예측 (선택 사항)
    if _sky_model is not None:
        try:
            sample_input = np.array([[u1_vec['ds'], u2_vec['ds']]])
            _ = _sky_model.predict(sample_input, verbose=0)
        except:
            pass

    return max(0, min(100, final_score))
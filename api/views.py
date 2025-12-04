# api/views.py

import json
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.request import Request

from profiles.models import UserProfile
from .saju_compatibility import calculate_compatibility_score
from .geo_utils import get_lat_lon, calculate_distance, get_distance_score
from .interest_utils import get_interest_score

User = get_user_model()


# 1. 사주 궁합 점수 조회 API
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def check_saju_compatibility(request, target_id):
    """
    [GET] ('api/match/score/<target_id>/'
    나와 상대방의 사주 궁합 점수 반환
    """
    try:
        # 1. 내 프로필 조회
        try:
            me = request.user.profile
        except AttributeError:
            return Response(
                {"error": "내 프로필이 존재하지 않습니다"},
                status=status.HTTP_404_NOT_FOUND
            )

        # 2. 상대방 프로필 조회
        target_user = get_object_or_404(User, id=target_id)
        try:
            target = target_user.profile
        except AttributeError:
            return Response(
                {"error": "상대방의 프로필이 존재하지 않습니다."},
                status=status.HTTP_404_NOT_FOUND
            )

        # 3. 본인과의 궁합 조회 예외 처리
        if request.user.id == target_id:
            return Response(
                {"error": "자신과의 궁합은 볼 수 없습니다."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 4. 궁합 점수 계산
        score = calculate_compatibility_score(me, target)

        return Response({
            "my_nickname": me.nickname,
            "partner_nickname": target.nickname,
            "compatibility_score": score,
            "message": "사주 궁합 분석이 완료되었습니다."
        }, status=status.HTTP_200_OK)
    except Exception as e:
        print(f"[Error] 궁합 분석 중 오류 발생: {e}")
        return Response(
            {"error": "분석 중 오류 발생했습니다."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_recommend_matches(request):
    """
    [GET] /api/match/recommend/
    나와 이성인 유저 중
    가중치 점수(사주+취향+거리)가 가장 높은 상위 10명을 반환
    [GET] /api/recommend/
    나와 이성(Opposite Gender)인 유저 중
    가중치 점수(사주+취향+거리)가 가장 높은 상위 10명을 반환합니다.
    """
    try:
        me = request.user.profile
        # 성별 정보 확인
        if not me.gender:
            return Response(
                {"error": "내 성별 정보가 없습니다."},
                status=status.HTTP_400_BAD_REQUEST
            )
    except AttributeError:
        return Response(
            {"error": "내 프로필 정보를 먼저 입력해주세요."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # 1. 이성 필터링 (남 -> 여 / 여 -> 남)
    target_gender = '여성' if me.gender == '남성' else '남성'

    # 2. 매칭 후보군 가져오기 (나 제외 + 이성만)
    candidates = UserProfile.objects.exclude(user=request.user).filter(gender=target_gender)

    match_results = []

    # 3. 점수 계산 Loop
    for target in candidates:
        try:
            # 사주 점수 (0.4)
            saju_score = calculate_compatibility_score(me, target)

            # 취향 점수 (0.5)
            interest_score = get_interest_score(me.hobbies, target.hobbies)

            # 거리 점수 (0.1)
            # 내 좌표 확인
            if me.latitude is not None and me.longitude is not None:
                my_coord = (me.latitude, me.longitude)
            else:
                my_coord = None

            # 상대 좌표 확인
            if target.latitude is not None and target.longitude is not None:
                target_coord = (target.latitude, target.longitude)
            else:
                target_coord = None

            # 거리 계산 (둘 다 좌표가 있을 때만)
            dist_km = 0
            geo_raw_score = 5 # 기본 점수

            if my_coord and target_coord:
                dist_km = calculate_distance(my_coord, target_coord)
                geo_raw_score = get_distance_score(dist_km)

            # 100점 만점 환산
            geo_score_100 = geo_raw_score * 10

            # 총점 계산
            # 사주(0.4) + 취향(0.5) + 거리(0.1)
            total_score = (saju_score * 0.4) + (interest_score * 0.5) + (geo_score_100 * 0.1)

            # 결과 리스트에 추가
            match_results.append({
                "user_id": target.user.id,
                "nickname": target.nickname,
                "gender": target.gender,
                "age": target.age if target.age else "?",
                "mbti": target.mbti,
                "job": target.job,
                "location": f"{target.location_city} {target.location_district}",
                "total_score": round(total_score, 1),
                "scores": {
                    "saju": saju_score,
                    "interest": interest_score,
                    "distance": geo_score_100
                },
                "info": {
                    "distance_km": f"{dist_km:.1f}km" if (my_coord and target_coord) else "알수없음",
                    "common_hobbies": list(set(me.hobbies or []) & set(target.hobbies or []))
                },
                "profile_image": target.images.first().image.url if target.images.exists() else None
            })

        except Exception as e:
            # 특정 유저 계산 중 에러가 나도 멈추지 않고 건너뜀 (서버 안정성)
            print(f"[Error] 사용자 {target.user.id} 매칭 계산 중 에러: {e}")
            continue

    # 4. 정렬 및 상위 10명 추출
    # 점수 높은 순(내림차순) 정렬
    match_results.sort(key=lambda x: x['total_score'], reverse=True)

    # 상위 10명 자르기
    top_10 = match_results[:10]

    return Response(top_10, status=status.HTTP_200_OK)


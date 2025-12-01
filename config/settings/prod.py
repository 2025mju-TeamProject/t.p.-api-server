# config/settings/prod.py (배포용 설정)

from datetime import timedelta

from config.settings.dev import SECRET_KEY

# JWT 설정
SIMPLE_JWT = {
    # Access Token 유효 기간: 30분
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),

    # Refresh Token 유효기간: 7일
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),

    # Refresh Token 갱신 시, 기존 Token 폐기 여부
    'ROTATE_REFRESH_TOKENS': True,

    # 폐기된 Refresh Token을 블랙리스트 처리하여 재사용 방지
    'BLACKLIST_AFTER_ROTATION': True,

    # 로그인 시, 업데이트 되는지 여부
    'UPDATE_LAST_LOGIN': False,

    # 암호화 알고리즘 (기본값 HS256)
    'ALGORITHM': 'HS256',

    # 서명 검증 키 (SECRET_KEY 사용)
    'SIGNING_KEY': SECRET_KEY,

    # 헤더 타입 (Authorization: Bearer <token>
    'AUTH_HEADER_TYPES': ('Bearer',),
}
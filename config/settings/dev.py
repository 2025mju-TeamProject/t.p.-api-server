# config/settings/dev.py
# TeamProject/TeamProject/settings/dev.py

# 1. base.py의 모든 설정을 가져옵니다.
from .base import *
from datetime import timedelta


# 2. base.py에서 잘라낸 설정들을 여기에 붙여넣습니다.
# (BASE_DIR이 base.py에 정의되어 있으므로 여기서도 사용 가능)

# Secret Key
localKeys = os.path.join(BASE_DIR, 'local.json') # 또는 secrets.json

with open(localKeys) as f:
    secrets = json.loads(f.read())

def get_secret(setting):
    """API 키 반환용"""
    try:
        return secrets[setting]
    except KeyError:
        error_msg = "Set the {} environment variable.".format(setting)
        raise ImproperlyConfigured(error_msg)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = get_secret('SECRET_KEY')

#API Keys
OPENAI_API_KEY = get_secret('OPENAI_API_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

SIMPLE_JWT = {
    # [개발용] 유효기간을 길게 설정 (로그인이 자주 풀리면 테스트하기 귀찮음)
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),

    # [개발용] 토큰 갱신 시 기존 Refresh Token을 계속 쓸 수 있게 함 (테스트 편의성)
    # Prod에서는 True로 해서 보안을 강화하지만, Dev에서는 False가 편합니다.
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': False,

    # 로그인 시 User 모델의 last_login 필드 업데이트 여부
    'UPDATE_LAST_LOGIN': True,

    # --- 아래는 기본 알고리즘 및 키 설정 (Prod와 동일하게 유지) ---
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,  # Django의 SECRET_KEY를 서명키로 사용
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 0,

    # 헤더 설정: Authorization: Bearer <token>
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',

    # 사용자 식별 기준
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',

    # 인증 규칙 (기본값)
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',

    # 토큰 클래스 설정 (기본값)
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',

    'JTI_CLAIM': 'jti',
}
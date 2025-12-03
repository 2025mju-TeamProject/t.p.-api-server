# chat/middleware.py

from urllib.parse import parse_qs
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

User = get_user_model()


@database_sync_to_async
def get_user(token_key):
    """
    동기(Sync) 방식의 DB 접근을 비동기(Async) 환경에서 실행하기 위한 함수
    """
    try:
        # 1. 토큰 디코딩 (유효성 검사 포함)
        access_token = AccessToken(token_key)
        user_id = access_token['user_id']

        # 2. 유저 조회
        user = User.objects.get(id=user_id)
        return user

    except (InvalidToken, TokenError) as e:
        return AnonymousUser()
    except User.DoesNotExist:
        return AnonymousUser()
    except Exception as e:
        return AnonymousUser()


class JwtAuthMiddleware:
    """
    WebSocket 연결 시 쿼리 스트링(?token=xxx)을 확인하여 인증하는 미들웨어
    """

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        # 1. 쿼리 스트링 파싱
        # scope['query_string']은 바이트(bytes) 형태이므로 디코딩 필요
        query_string = scope.get('query_string', b'').decode()
        query_params = parse_qs(query_string)

        # 2. 'token' 파라미터 추출 (리스트 형태라 첫 번째 값 가져옴)
        token = query_params.get('token', [None])[0]

        # 3. 토큰 유무에 따른 처리
        if token:
            scope['user'] = await get_user(token)
        else:
            scope['user'] = AnonymousUser()

        # 4. 다음 미들웨어 또는 컨슈머로 진행
        return await self.inner(scope, receive, send)
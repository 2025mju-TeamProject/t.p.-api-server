# config/asgi.py

import os
from django.core.asgi import get_asgi_application

# --- 채팅(Channels) 관련 임포트 ---
from channels.routing import ProtocolTypeRouter, URLRouter
# from channels.auth import AuthMiddlewareStack

# JWT 미들웨어
from chat.middleware import JwtAuthMiddleware
import chat.routing  # chat 앱의 routing.py를 불러옵니다.


# --- ✨ settings.py 분리 관련 수정 사항 ---
# TeamProject.settings가 아닌, TeamProject.settings.dev를 기본으로!
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')


# --- ✨ 채팅(Channels) 관련 라우팅 설정 ---
#
# 1. http:// 요청은 기존 Django 방식으로 (get_asgi_application() 사용)
# 2. ws:// 요청은 Channels 방식으로 (JwtAuthMiddleware/URLRouter 사용)
#
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": JwtAuthMiddleware(
        URLRouter(
            chat.routing.websocket_urlpatterns
        )
    ),
})
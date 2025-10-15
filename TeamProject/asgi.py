# TeamProject/asgi.py

import os
from django.core.asgi import get_asgi_application

# ✨ Channels와 관련된 import 문을 추가합니다.
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import chat.routing  # chat 앱에 우리가 만든 routing.py를 불러옵니다.

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TeamProject.settings')

# 기본 Django의 HTTP 애플리케이션을 불러옵니다.
django_asgi_app = get_asgi_application()

# ProtocolTypeRouter가 교통정리 담당관 역할을 합니다.
application = ProtocolTypeRouter({
    # 1. http:// 로 시작하는 요청이 오면, 기존의 Django 방식으로 처리합니다.
    "http": django_asgi_app,

    # 2. ws:// 로 시작하는 요청이 오면, Channels 방식으로 처리합니다.
    "websocket": AuthMiddlewareStack(  # 로그인 정보를 WebSocket에서도 사용하기 위함
        URLRouter(
            # chat/routing.py에 정의된 websocket_urlpatterns를 참조하여 길을 찾습니다.
            chat.routing.websocket_urlpatterns
        )
    ),
})
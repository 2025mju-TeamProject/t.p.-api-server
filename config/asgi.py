# config/asgi.py

import os
from django.core.asgi import get_asgi_application

django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from chat.middleware import JwtAuthMiddleware
import chat.routing  # chat 앱의 routing.py를 불러옵니다.


# TeamProject.settings가 아닌, TeamProject.settings.dev를 기본으로 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')


# 1. http:// 요청은 기존 Django 방식으로 (get_asgi_application() 사용)
# 2. ws:// 요청은 Channels 방식으로 (JwtAuthMiddleware/URLRouter 사용)
#
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JwtAuthMiddleware(
        URLRouter(
            chat.routing.websocket_urlpatterns
        )
    ),
})
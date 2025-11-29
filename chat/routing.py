# chat/routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # ws/chat/<room_name>/ 경로로 WebSocket 연결
    re_path(r"ws/chat/(?P<room_name>[-\w]+)/$", consumers.ChatConsumer.as_asgi()),
]

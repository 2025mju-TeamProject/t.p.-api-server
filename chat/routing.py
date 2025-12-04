# chat/routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # ws/chat/<target_id>/ 경로로 WebSocket 연결
    re_path(r"ws/chat/(?P<target_id>[-\w]+)/$", consumers.ChatConsumer.as_asgi()),
]
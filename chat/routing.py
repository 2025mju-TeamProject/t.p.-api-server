from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # ws/chat/상대방ID/ 형태의 WebSocket URL을 ChatConsumer와 연결
    re_path(r'ws/chat/(?P<other_user_id>\d+)/$', consumers.ChatConsumer.as_asgi()),
]
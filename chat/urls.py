# chat/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('<int:other_user_id>/', views.chat_room, name='chat_room'),

    path('api/messages/<str:room_name>/', views.MessageHistoryView.as_view(), name='message-history-api'),
    path('api/block/<int:user_id_to_block>/', views.BlockUserView.as_view(), name='block-user-api'),
    path('api/suggestions/<str:room_name>/', views.ChatSuggestionView.as_view(), name='chat-suggestions-api'),
    #post 메소드, 추천용 메소드
    path('api/rooms/', views.ChatRoomListView.as_view(), name='chat-room-list-api'),
]

# chat/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('api/history-messages/<int:target_id>/', views.MessageHistoryView.as_view(), name='message-history-api'),
    path('api/block/<int:user_id_to_block>/', views.BlockUserView.as_view(), name='block-user-api'),
    path('api/suggestions/<int:target_id>/', views.ChatSuggestionView.as_view(), name='chat-suggestions-api'),
    path('api/rooms/', views.ChatRoomListView.as_view(), name='chat-room-list-api'),
    path('api/send-messages/<int:target_id>/', views.MessageSendView.as_view(), name='message-send')
]

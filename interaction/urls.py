# interaction/urls.py

from django.urls import path

from .views import UserLikeView, LikeListView

urlpatterns = [
    # 하트 보내기: (POST /api/interaction/like/3/)
    path('like/<int:receiver_id>/', UserLikeView.as_view(), name='send-like'),

    # 목록 보기: (GET /api/interaction/likes/?type=rerceived 이거나 sent)
    path('likes/', LikeListView.as_view(), name='like-list')
]
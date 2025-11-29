# api/urls.py

from django.urls import path
from . import views  # 현재 폴더(api)에 있는 views.py를 불러오기

urlpatterns = [
    path('compatibility/<int:target_id>/', views.check_saju_compatibility, name='check_saju'),
    path('match/recommend/', views.get_recommend_matches, name='recommend_matches'),
]

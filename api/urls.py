# api/urls.py

from django.urls import path
from . import views  # 현재 폴더(api)에 있는 views.py를 불러오기
from profiles.views import (
    UserRegistrationView,
    MyTokenObtainPairView,
    ProfileView,
    get_saju_api
)

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('saju/', get_saju_api, name='get_saju_api'),
    path('match/score/<int:target_id>/', views.check_saju_compatibility, name='check_saju'),
    path('recommend/', views.get_recommend_matches, name='recommend_matches'),
]
# api/urls.py (새로 만드는 파일)

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
    path('token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('saju/', get_saju_api, name='get_saju_api'),
]
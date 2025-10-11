# api/urls.py (새로 만드는 파일)

from django.urls import path
from . import views  # 현재 폴더(api)에 있는 views.py를 불러오기

urlpatterns = [
    # http://127.0.0.1:8000/api/profile/ 주소로 요청이 오면 views.py의 generate_profile 함수를 실행
    path('profile/', views.generate_profile, name='generate_profile'),

    # http://127.0.0.1:8000/api/report/ 주소로 요청이 오면 views.py의 generate_compatibility_report 함수를 실행
    path('report/', views.generate_compatibility_report, name='generate_compatibility_report'),

    # http://127.0.0.1:8000/api/conversation/ 주소로 요청이 오면 views.py의 generate_conversation_starter 함수를 실행
    path('conversation/', views.generate_conversation_starter, name='generate_conversation_starter'),

    path('saju/', views.get_saju_api, name='get_saju_api'),
]
# profiles/urls.py

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views
urlpatterns = [
    # 1. 회원가입 (POST /api/users/register/)
    path('register/', views.UserRegistrationView.as_view(), name='register'),

    # 2. 로그인 (POST /api/users/login/)
    path('login/', views.MyTokenObtainPairView.as_view(), name='login'),

    # 3. Refresh Token 보냄 (POST /api/uses/refresh/)
    path('login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # 4. 내 프로필 조회/생성/수정 (GET, POST, PATCH /api/users/profile/)
    path('profile/', views.ProfileView.as_view(), name='my_profile'),
    path('profile/regenerate/', views.ProfileRegenerateView.as_view(), name='profile_regenerate'),

    # 5. 타인 프로필 상세 조회 (GET /api/users/<user_id>/)
    # 예: /api/users/3/
    path('<int:user_id>/', views.UserProfileDetailView.as_view(), name='user_profile_detail'),

    # 6. 사주 만세력 계산 전용 (POST /api/users/saju/)
    path('saju/', views.get_saju_api, name='get_saju'),

    # 7. 매칭 한 줄 평 AI 생성 (POST /api/users/match-summary/<id>/)
    path('match-summary/<int:other_user_id>/', views.MatchSummaryView.as_view(), name='match_summary'),

    # 8. 프로필에서 사용자 신고 (POST /api/users/report/<id>/)
    path('report/<int:user_id>/', views.report_user, name='report_user'),

    # 9. 채팅방에서 사용자 신고 (POST /api/report/chat/<room_name>/
    path('report/chat/<str:room_name>/', views.report_chat_user, name='report_chat_user'),

    # 9. 회원 궁합 점수 조회 (GET /api/match/score/<target_id>/
    path('match/score/<int:other_user_id>/', views.MatchSummaryView.as_view(), name='match-summary'),

    # 10. 유저 프로필 유무 확인 (GET /api/users/status/)
    path('status/', views.UserStatusCheckView.as_view(), name='user-status-check'),

]

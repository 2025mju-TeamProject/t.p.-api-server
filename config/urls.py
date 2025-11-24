from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from rest_framework_simplejwt.views import TokenRefreshView
from django.contrib.auth import views as auth_views

from profiles.views import MyTokenObtainPairView

urlpatterns = [
    path('admin/', admin.site.urls),
    # 'api/'로 시작하는 모든 주소는 이제 api/urls.py 파일에서 관리하라는 의미
    path('api/', include('api.urls')),
    # chat 앱의 urls.py를 포함
    path('chat/', include('chat.urls')),

    # 세션 로그인/로그아웃
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),

    # POST /api/token/ (로그인)
    path('api/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),

    # POST /api/token/refresh/ (토큰 리프레시)
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

# DEBUG 모드 시, 업로드 된 미디어 파일 서빙
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

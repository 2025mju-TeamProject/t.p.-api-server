from django.contrib import admin
from django.urls import path, include

from rest_framework_simplejwt.views import TokenRefreshView

from api.views import MyTokenObtainPairView

urlpatterns = [
    path('admin/', admin.site.urls),
    # 'api/'로 시작하는 모든 주소는 이제 api/urls.py 파일에서 관리하라는 의미
    path('api/', include('api.urls')),
    # chat 앱의 urls.py를 포함
    path('chat/', include('chat.urls')),

    # POST /api/token/ (Login)
    path('api/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),

    # POST /api/token/refresh/ (Token Refresh)
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

# profiles/urls.py

from django.urls import path
from .views import UserReportCreateView

urlpatterns = [
    # ... 기존 URL들 ...

    # 사용자 신고 API
    path('report/<int:user_id>/', UserReportCreateView.as_view(), name='report_user'),
]
# profiles/admin.py

from django.contrib import admin
from .models import UserProfile, ProfileImage, UserReport

# 기존 프로필 관련 Admin 설정
class ProfileImageInline(admin.TabularInline):
    model = ProfileImage
    extra = 1

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    inlines = [ProfileImageInline]
    list_display = ['user', 'nickname', 'gender', 'year', 'location_city']

# 신고 내역 관리자 설정
@admin.register(UserReport)
class UserReportAdmin(admin.ModelAdmin):
    list_display = ['id', 'status', 'reporter', 'reported_user', 'reason', 'source', 'created_at']
    list_filter = ['status', 'reason', 'source', 'created_at']
    search_fields = ['reporter__username', 'reported_user__username', 'desscription']
    ordering = ['-created_at']

    # Admin 페이지에서 처리상태만 수정가능
    list_editable = ['status']
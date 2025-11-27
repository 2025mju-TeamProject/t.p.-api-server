# config/wsgi.py
# TeamProject/TeamProject/wsgi.py (최종본)

import os
from django.core.wsgi import get_wsgi_application

# --- ✨ settings.py 분리 관련 수정 사항 ---
# TeamProject.settings가 아닌, TeamProject.settings.dev를 기본으로!
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

# --- 기존 WSGI 애플리케이션 로드 ---
application = get_wsgi_application()
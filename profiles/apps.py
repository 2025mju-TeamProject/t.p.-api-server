# profiles/apps.py

from django.apps import AppConfig

class ProfilesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'profiles'

    # 시그널(자동 프로필 생성)을 쓴다면 아래 코드가 필요할 수 있습니다.
    def ready(self):
        # import profiles.signals
        pass
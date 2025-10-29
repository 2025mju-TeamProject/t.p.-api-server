# TeamProject/TeamProject/settings/dev.py

# 1. base.py의 모든 설정을 가져옵니다.
from .base import *

# 2. base.py에서 잘라낸 설정들을 여기에 붙여넣습니다.
# (BASE_DIR이 base.py에 정의되어 있으므로 여기서도 사용 가능)

# Secret Key
localKeys = os.path.join(BASE_DIR, 'local.json') # 또는 secrets.json

with open(localKeys) as f:
    secrets = json.loads(f.read())

def get_secret(setting):
    """API 키 반환용"""
    try:
        return secrets[setting]
    except KeyError:
        error_msg = "Set the {} environment variable.".format(setting)
        raise ImproperlyConfigured(error_msg)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = get_secret('SECRET_KEY')

#API Keys
OPENAI_API_KEY = get_secret('OPENAI_API_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []
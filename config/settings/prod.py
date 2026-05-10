from .base import *
from .db import build_mariadb_database


def _csv_env(name, default=''):
	raw = os.getenv(name, default)
	return [value.strip() for value in raw.split(',') if value.strip()]


DEBUG = False
DISABLE_LOGIN_REQUIRED = False
ALLOWED_HOSTS = _csv_env(
	'DJANGO_ALLOWED_HOSTS',
	'127.0.0.1,localhost,192.168.0.250,.synology.me,.snology.me'
)
CSRF_TRUSTED_ORIGINS = _csv_env(
	'DJANGO_CSRF_TRUSTED_ORIGINS',
	'http://jakesto.synology.me:8090,http://jakesto.snology.me:8090'
)
STATIC_ROOT = BASE_DIR / 'staticfiles'

DATABASES = {
	'default': build_mariadb_database(default_target='nas')
}

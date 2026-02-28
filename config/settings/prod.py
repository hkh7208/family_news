from .base import *
from .db import build_mariadb_database

DEBUG = False
ALLOWED_HOSTS = [host.strip() for host in os.getenv('DJANGO_ALLOWED_HOSTS', '').split(',') if host.strip()]
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in os.getenv('DJANGO_CSRF_TRUSTED_ORIGINS', '').split(',') if origin.strip()]
STATIC_ROOT = BASE_DIR / 'staticfiles'

DATABASES = {
	'default': build_mariadb_database(default_target='nas')
}

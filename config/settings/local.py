# config/settings/local.py
from .base import *
from .db import build_mariadb_database


def _csv_env(name, default=''):
    raw = os.getenv(name, default)
    return [value.strip() for value in raw.split(',') if value.strip()]

DEBUG = True
ALLOWED_HOSTS = _csv_env('DJANGO_ALLOWED_HOSTS', '127.0.0.1,localhost,192.168.0.107')
DISABLE_LOGIN_REQUIRED = False

DATABASES = {
    'default': build_mariadb_database(default_target='local')
}
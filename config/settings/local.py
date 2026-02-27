# config/settings/local.py
from .base import *
from .db import build_mariadb_database

DEBUG = True
ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
    '192.168.0.107',
]

DATABASES = {
    'default': build_mariadb_database(default_target='local')
}
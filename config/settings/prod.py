from .base import *
from .db import build_mariadb_database

DEBUG = False
ALLOWED_HOSTS = [host.strip() for host in os.getenv('DJANGO_ALLOWED_HOSTS', '').split(',') if host.strip()]

DATABASES = {
	'default': build_mariadb_database(default_target='nas')
}

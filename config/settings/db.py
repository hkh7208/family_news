import os


def _as_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def build_mariadb_database(default_target='local'):
    target = (os.getenv('DB_TARGET', default_target) or default_target).lower()
    prefix = 'NAS_DB_' if target == 'nas' else 'LOCAL_DB_'

    name = os.getenv(f'{prefix}NAME', os.getenv('DB_NAME', 'family_news'))
    user = os.getenv(f'{prefix}USER', os.getenv('DB_USER', 'family_news'))
    password = os.getenv(f'{prefix}PASSWORD', os.getenv('DB_PASSWORD', ''))
    host = os.getenv(f'{prefix}HOST', os.getenv('DB_HOST', '127.0.0.1'))
    port = os.getenv(f'{prefix}PORT', os.getenv('DB_PORT', '3306'))

    return {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': name,
        'USER': user,
        'PASSWORD': password,
        'HOST': host,
        'PORT': port,
        'CONN_MAX_AGE': _as_int(os.getenv('DB_CONN_MAX_AGE', '60'), 60),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
# Django settings for admin project.

DEBUG = False

ADMINS = (
   ('PostgreSQL Webmaster', 'webmaster@postgresql.org'),
)

MANAGERS = ADMINS

DATABASE_ENGINE = 'postgresql_psycopg2'           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = 'planetbeta'             # Or path to database file if using sqlite3.
DATABASE_USER = 'admin'             # Not used with sqlite3.
DATABASE_PASSWORD = ''         # Not used with sqlite3.
DATABASE_HOST = '/tmp'             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

TIME_ZONE = 'GMT'
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

USE_I18N = False

MEDIA_ROOT = ''
MEDIA_URL = ''
ADMIN_MEDIA_PREFIX = '/media/'

SECRET_KEY = '_q-piuw^kw^v1f%b6nrla+p%=&1bt#z%c$ujhioxe^!z%8q1l0'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'hamnadmin.exceptions.PlanetExceptionMiddleware',
)

ROOT_URLCONF = 'hamnadmin.urls'

TEMPLATE_DIRS = (
    # Refer back to main planet templates
    "../template",
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'hamnadmin.register',
)

AUTHENTICATION_BACKENDS = (
    'hamnadmin.auth.AuthBackend',
)

LOGIN_URL = '/register/login'

# If there is a local_settings.py, let it override our settings
try:
	from local_settings import *
except:
	pass


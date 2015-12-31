# Django settings for admin project.

DEBUG = False

ADMINS = (
   ('PostgreSQL Webmaster', 'webmaster@postgresql.org'),
)

MANAGERS = ADMINS

DATABASES={
	'default': {
		'ENGINE': 'django.db.backends.postgresql_psycopg2',
		'NAME': 'planetbeta',
		'USER': 'admin',
		}
	}

TIME_ZONE = 'GMT'
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

USE_I18N = False

MEDIA_ROOT = ''
MEDIA_URL = ''
STATIC_URL = '/media/'

SECRET_KEY = '_q-piuw^kw^v1f%b6nrla+p%=&1bt#z%c$ujhioxe^!z%8q1l0'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
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
	'django.contrib.staticfiles',
    'hamnadmin.register',
    'django.contrib.admin',
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


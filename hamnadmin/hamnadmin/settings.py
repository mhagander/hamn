# Django settings for admin project.
import os

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
	'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
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
	'django.contrib.staticfiles',
    'hamnadmin.register',
    'hamnadmin.mailqueue',
    'django.contrib.admin',
)

AUTHENTICATION_BACKENDS = (
    'hamnadmin.auth.AuthBackend',
)

LOGIN_URL = '/register/login'

ALLOWED_HOSTS=['*']

EMAIL_SENDER='planet@postgresql.org'
NOTIFICATION_RECEIVER='planet@postgresql.org'

# Set to None for testing
VARNISH_URL="http://localhost/varnish-purge"

# Dynamically load settings from the "outer" planet.ini that might
# be needed.
try:
	import ConfigParser
	_configparser = ConfigParser.ConfigParser()
	_configparser.read(os.path.join(os.path.abspath(os.path.dirname(__file__)), '../../planet.ini'))
	TWITTER_CLIENT=_configparser.get('twitter', 'consumer')
	TWITTER_CLIENTSECRET=_configparser.get('twitter', 'consumersecret')
	TWITTER_TOKEN=_configparser.get('twitter', 'token')
	TWITTER_TOKENSECRET=_configparser.get('twitter', 'secret')
except:
	TWITTER_CLIENT=None
	TWITTER_CLIENTSECRET=None
	TWITTER_TOKEN=None
	TWITTER_TOKENSECRET=None

# If there is a local_settings.py, let it override our settings
try:
	from local_settings import *
except:
	pass


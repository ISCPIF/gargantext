"""
Django settings for gargantext_web project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
PROJECT_PATH = os.path.join(BASE_DIR, os.pardir)
PROJECT_PATH = os.path.abspath(PROJECT_PATH)


######################################################################
# ASYNCHRONOUS TASKS

import djcelery
djcelery.setup_loader()
BROKER_URL = 'amqp://guest:guest@localhost:5672/'

CELERY_IMPORTS=("node.models","gargantext_web.celery")


#
#from celery import Celery
#
#app = Celery('gargantext_web')
#
#app.conf.update(
#    CELERY_RESULT_BACKEND='djcelery.backends.database:DatabaseBackend',
#)
#
#
#app.conf.update(
#    CELERY_RESULT_BACKEND='djcelery.backends.cache:CacheBackend',
#)
#

######################################################################

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'bt)3n9v&a02cu7^^=+u_t2tmn8ex5fvx8$x4r*j*pb1yawd+rz'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
MAINTENANCE = False

TEMPLATE_DEBUG = False

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes
    # Don't forget to use absolute paths, not relative paths.
    '/srv/gargantext/templates',
)


#ALLOWED_HOSTS = ['*',]
ALLOWED_HOSTS = ['localhost',
                'gargantext.org',
                'stable.gargantext.org',
                'dev.gargantext.org',
                'iscpif.gargantext.org',
                'gargantext.iscpif.fr',
                'mines.gargantext.org',
                'pasteur.gargantext.org',
                'beta.gargantext.org',
                'garg-dev.iscpif.fr',
                'garg-stable.iscpif.fr',
                ]


# Application definition

INSTALLED_APPS = (
    'grappelli',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'django_pg',
    'cte_tree',
    'node',
    'ngram',
    'annotations',
    'scrappers.scrap_pubmed',
    'djcelery',
    'aldjemy',
    'rest_framework',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

REST_SESSION_LOGIN = False
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
   'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny',
    ),
}

WSGI_APPLICATION = 'wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'gargandb_set',
        'USER': 'gargantua',
        'PASSWORD': 'C8kdcUrAQy66U',
        #'USER': 'gargantext',
        #'PASSWORD': 'C8krdcURAQy99U',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}


# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

ROOT_URLCONF = 'gargantext_web.urls'

STATIC_ROOT = '/var/www/gargantext/static/'
STATIC_URL = '/static/'

MEDIA_ROOT = '/var/www/gargantext/media'
#MEDIA_ROOT = os.path.join(PROJECT_PATH, 'media')
MEDIA_URL   = '/media/'


STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'django.contrib.staticfiles.finders.FileSystemFinder',
)


STATICFILES_DIRS = (
            #os.path.join(BASE_DIR, "static"),
                '/srv/gargantext/static',
                #'/var/www/www/alexandre/media',
                #'/var/www/alexandre.delanoe.org/',
                )

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.request",
    "django.core.context_processors.static",
)

LOGIN_URL = '/auth/'

# grappelli custom
GRAPPELLI_ADMIN_TITLE = "Gargantext"

if DEBUG is True or 'GARGANTEXT_DEBUG' in os.environ:
    try:
        from gargantext_web.local_settings import *
    except ImportError:
        pass

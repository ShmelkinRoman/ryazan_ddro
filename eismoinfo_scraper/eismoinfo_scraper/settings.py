# flake8: noqa
import os
import environ

from pathlib import Path

env = environ.Env(
    # This line specifies that the DEBUG variable should be treated as a boolean. 
    # If the environment variable is not set, it defaults to False.
    DEBUG=(bool, False)
)


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Take environment variables from .env file
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-(5(wdd#i07sq&8j#tq53-vn^5#0x=uo7^c_ut3&m1)dcekq#+z'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')

ALLOWED_HOSTS = ['eismoinfo-app', 'localhost', '127.0.0.1', '91.228.154.192', '89.248.192.136', 'blackwaterpark.ddns.net']


# Application definition

INSTALLED_APPS = [
    'api_scraper.apps.ApiScraperConfig',
    'weatherdata_api.apps.WeatherdataApiConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_celery_beat',
    'rest_framework',
    'rest_framework.authtoken',
    'django_prometheus',
    'drf_yasg',
    'corsheaders'
]

MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django_prometheus.middleware.PrometheusAfterMiddleware'
]

ROOT_URLCONF = 'eismoinfo_scraper.urls'  # Главный urls.

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'eismoinfo_scraper.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases
# if DEBUG:
#     DATABASES = {
#         'default': {
#             'ENGINE': 'django_prometheus.db.backends.sqlite3',
#             'NAME': BASE_DIR / 'db.sqlite3',
#         }
#     }
# else:
DATABASES = {
    'default': {
        'ENGINE': 'django_prometheus.db.backends.postgresql',
        'NAME': env('POSTGRES_DB'),   # Your database name
        'USER': env('POSTGRES_USER'),     # Default PostgreSQL user
        'PASSWORD': env('POSTGRES_PASSWORD'),        # Add your password if set (default is empty)
        'HOST': 'db',    # Set to localhost for local development
        'PORT': '5432',         # Default PostgreSQL port
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR,'collectedstatic/')

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Redis host.
# if DEBUG:
#     REDIS_HOST = 'localhost'
# else:
REDIS_HOST = 'redis'

REDIS_PORT = '6379'
REDIS_DB = '0'

# Celery variables.
CELERY_RESULT_BACKEND = f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'
CELERY_BROKER_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'

CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated', 
    ],

    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ]
}

DOMAIN_NAME = env('DOMAIN_NAME')
GERMAN_SERVER_IP = env('GERMAN_SERVER_IP')
HARVESTER_SERVER_IP = env('HARVESTER_SERVER_IP')

# Для избежания глюка со входом в админку после деплоя.
CSRF_TRUSTED_ORIGINS = [DOMAIN_NAME, 'http://localhost', 'http://127.0.0.1', GERMAN_SERVER_IP, HARVESTER_SERVER_IP]


CORS_ALLOWED_ORIGINS = [DOMAIN_NAME, 'http://localhost', 'http://127.0.0.1', GERMAN_SERVER_IP, HARVESTER_SERVER_IP]

CORS_ALLOW_ALL_ORIGINS = True

SWAGGER_SETTINGS = {
   'USE_SESSION_AUTH': False
}

PROMETHEUS_EXPORT_MIGRATIONS =  True

"""
Base settings for data_platform project.
"""
from pathlib import Path
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-this-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party apps
    'rest_framework',
    'corsheaders',
    'django_filters',
    'drf_spectacular',
    'django_celery_beat',
    'simple_history',

    # Local apps
    'apps.core',
    'apps.data_aggregation',
    'apps.data_acquisition',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'config.wsgi.application'

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='data_platform'),
        'USER': config('DB_USER', default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default='postgres'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators
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
# https://docs.djangoproject.com/en/5.2/topics/i18n/
LANGUAGE_CODE = 'ja'

TIME_ZONE = config('TIMEZONE', default='Asia/Tokyo')

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 100,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# DRF Spectacular Settings
SPECTACULAR_SETTINGS = {
    'TITLE': 'Data Consolidation Platform API',
    'DESCRIPTION': 'API for data aggregation and acquisition platform',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

# CORS Settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
]

# CSRF Settings
# Required for HTTPS origins (Django 4.0+)
CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default='https://data.yamaguchi.lan,http://localhost:8000,http://127.0.0.1:8000'
).split(',')

# Celery Configuration
REDIS_HOST = config('REDIS_HOST', default='localhost')
REDIS_PORT = config('REDIS_PORT', default='6379')
REDIS_DB_AGGREGATION = config('REDIS_DB_AGGREGATION', default='0')
REDIS_DB_ACQUISITION = config('REDIS_DB_ACQUISITION', default='1')

# Celery settings will be configured in each app's celery.py
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = True
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

# Nextcloud WebDAV Configuration
# For Docker: use 'nextcloud-web' container name (nginx frontend)
# For local dev: use 'http://localhost/remote.php/dav/files/admin/'
NEXTCLOUD_WEBDAV_URL = config(
    'NEXTCLOUD_WEBDAV_URL',
    default='http://nextcloud-web/remote.php/dav/files/admin/'
)
NEXTCLOUD_USERNAME = config('NEXTCLOUD_USERNAME', default='admin')
NEXTCLOUD_PASSWORD = config('NEXTCLOUD_PASSWORD', default='')
NEXTCLOUD_TIMEOUT = config('NEXTCLOUD_TIMEOUT', default=30, cast=int)

# Nextcloud Webhook Configuration
NEXTCLOUD_WEBHOOK_TOKEN = config(
    'NEXTCLOUD_WEBHOOK_TOKEN',
    default='change-this-to-a-secure-random-token'
)

# OnlyOffice Configuration
ONLYOFFICE_SERVER = config('ONLYOFFICE_SERVER', default='http://onlyoffice/')
ONLYOFFICE_SECRET = config('ONLYOFFICE_SECRET', default='tDCVy4C0oUPWjEXCvCZ4KnFe7N7z5V')

# OnlyOffice Callback Security
# For testing: empty string allows all IPs
# Production: use specific CIDR ranges like '172.18.0.0/16'
ALLOWED_CALLBACK_IPS = config(
    'ALLOWED_CALLBACK_IPS',
    default=''  # Empty = allow all (testing only)
).split(',') if config('ALLOWED_CALLBACK_IPS', default='') else []

# Nextcloud Callback URL (for forwarding from Django)
NEXTCLOUD_CALLBACK_BASE_URL = config(
    'NEXTCLOUD_CALLBACK_BASE_URL',
    default='http://cloud.yamaguchi.lan'
)

# Nextcloud Configuration for Data Export
NEXTCLOUD_CONFIG = {
    'webdav_hostname': 'http://nextcloud-web/remote.php/dav/files/Data-Platform/',
    'webdav_login': 'Data-Platform',
    'webdav_password': 'DACZ7-8aYLi-SAJck-Q3tTR-Aie5B',
}

# Excel Output Path Configuration
# Historical tracking: files with timestamp in data_platform/ folder
EXCEL_OUTPUT_PATH = 'data_platform/'

# Non-historical tracking: overwrite files in No_aggregated_raw_data/ folder
EXCEL_OUTPUT_PATH_NO_HISTORY = 'No_aggregated_raw_data/'

# Dashboard output path for Data_Dashboard folder
EXCEL_OUTPUT_PATH_DASHBOARD = 'Data_Dashboard/'

# Enable/disable historical tracking (timestamped files)
# Set to False to disable historical tracking and only keep latest version
ENABLE_EXCEL_HISTORICAL_TRACKING = config('ENABLE_EXCEL_HISTORICAL_TRACKING', default=True, cast=bool)

# Batch Stats API Token
# Simple token authentication for batch encoding stats API
BATCH_STATS_API_TOKEN = config('BATCH_STATS_API_TOKEN', default='FAZEHBZu0g2o3sRfQ58MxRC0w0htdUoPaLDN8R3ku8dJxk5exDgEUC1GtbJhwWWJKr4s8E')


# WebScraper Cloud API 访问令牌（在 Web Scraper Cloud 的 API 页面可见）
WEB_SCRAPER_API_TOKEN = "YNndD5WeM3UFO32RKdrogf2p4hNVPlZE3r3rLCoHD3B4idpJcjyqRJbNndXM"

# 导出地址模板（如官方变更，可在这里改）
# WEB_SCRAPER_EXPORT_URL_TEMPLATE = "https://api.webscraper.io/api/v1/scraping-job/{job_id}/csv?api_token=vrbBYdfX805GgpQoDfgyPcm45QMoEx6ygvkfHohjo3CJBky7qO0oiFbXUjAp"
WEB_SCRAPER_EXPORT_URL_TEMPLATE = "https://api.webscraper.io/api/v1/scraping-job/{job_id}/csv"

# Webhook 共享密钥：在 WebScraper Cloud 的 webhook URL 上带 ?token=XXXX，或在 Header 里带 X-Webhook-Token
WEB_SCRAPER_WEBHOOK_TOKEN = "0BkhVQJQPDe4IPfxfnw9bX8hYzxY29D48uGi8zq8TcjbsMIvXShEzaEJFFAj"

# 可选：把 WebScraper 的 sitemap 名 或 job 上的 custom_id 映射为清洗器名（shop3/shop4…）
WEB_SCRAPER_SOURCE_MAP = {
    "official_website_redirect_to_yamato_tracking": "official_website_redirect_to_yamato_tracking",
    "redirect_to_japan_post_tracking": "redirect_to_japan_post_tracking",
    "official_website_tracking": "official_website_tracking",
    "yamato_tracking_only": "yamato_tracking_only",
    "japan_post_tracking_only": "japan_post_tracking_only",
    "japan-post-10": "japan_post_tracking_10",
}

# Delivery Status Query Interval Configuration
# Minimum time interval (in hours) between delivery status queries for the same Purchasing record
# This prevents excessive queries to tracking services
DELIVERY_STATUS_QUERY_INTERVAL_HOURS = config(
    'DELIVERY_STATUS_QUERY_INTERVAL_HOURS',
    default=1,
    cast=int
)

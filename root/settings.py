import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv('.env')

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')

DEBUG = False

ALLOWED_HOSTS = ['edumrx-1.onrender.com', '127.0.0.1', 'localhost', "edumrx.uz", ".edumrx.uz"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    'corsheaders',
    'apps',
    "rest_framework",
    'rest_framework_simplejwt',
    'drf_spectacular',
    'django_filters',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "root.urls"
AUTH_USER_MODEL = 'apps.User'

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "root.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv('POSTGRES_NAME'),
        "USER": os.getenv("POSTGRES_USER"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD"),
        "HOST": os.getenv("POSTGRES_HOST"),
        "PORT": os.getenv("POSTGRES_PORT"),
    }
}
REDIS_URL = os.getenv("REDIS_URL", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'uz'

TIME_ZONE = "Asia/Tashkent"

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "media")

SUPABASE_PUBLIC_URL = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/"


if 'storages' not in INSTALLED_APPS:
    INSTALLED_APPS += ['storages']

AWS_ACCESS_KEY_ID = os.getenv('SUPABASE_SERVICE_KEY')
AWS_SECRET_ACCESS_KEY = os.getenv('SUPABASE_SERVICE_KEY')
AWS_STORAGE_BUCKET_NAME = os.getenv('SUPABASE_BUCKET')
AWS_S3_ENDPOINT_URL = f"{os.getenv('SUPABASE_URL')}/storage/v1/s3"

# Muhim: Supabase bilan to'g'ri ishlash sozlamalari
AWS_S3_FILE_OVERWRITE = False
AWS_S3_ADDRESSING_STYLE = 'path'
AWS_QUERYSTRING_AUTH = False  # URL oxiriga tokenlar qo'shilishini taqiqlaydi
AWS_DEFAULT_ACL = None        # Supabase uchun majburiy None bo'lishi shart!

# Standart saqlash tizimini S3 ga o'tkazish
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

# Next.js va brauzerlar uchun toza ommaviy URL generatori
_SUPABASE_URL_CLEAN = os.getenv('SUPABASE_URL', '').rstrip('/')
_SUPABASE_BUCKET_CLEAN = os.getenv('SUPABASE_BUCKET', '').strip('/')
MEDIA_URL = f"{_SUPABASE_URL_CLEAN}/storage/v1/object/public/{_SUPABASE_BUCKET_CLEAN}/"

REST_FRAMEWORK = {
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PAGINATION_CLASS': 'apps.pagination.CustomPagination',
    'PAGE_SIZE': 20,
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'EduX API',
    'VERSION': '1.0.0',
    'TAGS': [
        {'name': 'Auth'},
        {'name': 'Profile'},
        {'name': 'SuperAdminDashboard'},
        {'name': 'SuperAdminCenter'},
        {'name': 'SuperAdminDirector'},
        {'name': 'SuperAdminTeacher'},
        {'name': 'SuperAdminStudent'},
        {'name': 'AdminDashboard'},
        {'name': 'ManagementTeacher'},
        {'name': 'ManagementStudent'},
        {'name': 'ManagementAttendance'},
        {'name': 'StudentDashboard'},
        {'name': 'Group'},
        {'name': 'GroupStudents'},
        {'name': 'Room'},
        {'name': 'Notifications'},
    ]
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=5),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=5),
}

APPEND_SLASH = False

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://edu-x-henna.vercel.app",
    "https://edumrx.uz",
    "https://.edumrx.uz",
    "https://edu-x-henna.vercel.app",
    "https://edumrx.uz",
    "https://admin.edumrx.uz",
]
CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = [
    "https://admin.edumrx.uz",
    "https://edumrx-1.onrender.com",
    "https://edumrx.uz",
    "https://.edumrx.uz",
    "http://localhost:3000",
    "https://edumrx.uz",
    "https://www.edumrx.uz",
    "http://localhost:3000",
]

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER


STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

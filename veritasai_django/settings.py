"""
Django settings for veritasai_django project.
Tương đương với config/ trong Laravel
"""

import os
from pathlib import Path
import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Initialize environment variables (tương đương với .env trong Laravel)
env = environ.Env(
    DEBUG=(bool, True)
)

# Read .env file
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY', default='django-insecure-change-this-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG', default=True)

ALLOWED_HOSTS = ['*']  # Trong production, nên specify cụ thể

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',  # Admin panel (tương đương Laravel Nova)
    'django.contrib.auth',    # Authentication (tương đương Laravel Breeze)
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party
    'rest_framework',  # Django REST Framework cho API
    'corsheaders',     # CORS support
    
    # Local apps
    'app.apps.AppConfig',  # Main app
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # CORS middleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'veritasai_django.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # Templates directory (tương đương resources/views trong Laravel)
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

WSGI_APPLICATION = 'veritasai_django.wsgi.application'

# Database (tương đương với config/database.php trong Laravel)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME', default='veritasai_python'),
        'USER': env('DB_USER', default='postgres'),
        'PASSWORD': env('DB_PASSWORD', default='password'),
        'HOST': env('DB_HOST', default='localhost'),
        'PORT': env('DB_PORT', default='5432'),
        # Connection Pooling for better performance
        'CONN_MAX_AGE': 600,  # Keep connections alive for 10 minutes
        'OPTIONS': {
            'connect_timeout': 10,
        },
    }
}

# Password validation (tương đương với Laravel validation)
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
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images) (tương đương với Laravel public/)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    # BASE_DIR / 'static',  # Tạm thời comment vì chưa có thư mục
]

# Media files (tương đương với Laravel storage/app/public)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model (tạm thời dùng default, sẽ customize sau)
# AUTH_USER_MODEL = 'app.User'  # Uncomment sau khi có migrations

# Django REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',  # Cho phép access trong development
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20
}

# CORS settings (tương đương với Laravel CORS config)
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
]

CORS_ALLOW_ALL_ORIGINS = DEBUG  # Chỉ trong development

# Celery Configuration (tương đương với config/queue.php trong Laravel)
CELERY_BROKER_URL = env('REDIS_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = env('REDIS_URL', default='redis://localhost:6379/0')

# Cache Configuration (tương đương với config/cache.php trong Laravel)
# Using Redis for caching (embeddings, etc.)
# Fallback to LocMemCache if Redis not available
try:
    import redis
    redis_available = True
except ImportError:
    redis_available = False

if redis_available:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': env('REDIS_URL', default='redis://localhost:6379/1'),
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'IGNORE_EXCEPTIONS': True,  # Fallback nếu Redis fail
            },
            'KEY_PREFIX': 'veritasai',
            'TIMEOUT': 3600,
        }
    }
else:
    # Fallback to memory cache if Redis not available
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'veritasai-cache',
        }
    }

# App-specific settings (tương đương với config/services.php trong Laravel)
OLLAMA_BASE_URL = env('OLLAMA_BASE_URL', default='http://127.0.0.1:11434')
OLLAMA_EMBED_MODEL = env('OLLAMA_EMBED_MODEL', default='nomic-embed-text')
OLLAMA_CHAT_MODEL = env('OLLAMA_CHAT_MODEL', default='llama3.1')
STORAGE_PATH = env('STORAGE_PATH', default=str(BASE_DIR / 'storage'))


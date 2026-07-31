'''Django settings for the ENGP project.'''

from pathlib import Path

import environ


BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env()
ENV_FILE = BASE_DIR / '.env'

if ENV_FILE.exists():
    environ.Env.read_env(ENV_FILE)


SECRET_KEY = env('SECRET_KEY', default='dev-only-change-me')
DEBUG = env.bool('DEBUG', default=True)
ALLOWED_HOSTS = env.list(
    'ALLOWED_HOSTS',
    default=['localhost', '127.0.0.1', 'engp.localhost'],
)
CSRF_TRUSTED_ORIGINS = env.list(
    'CSRF_TRUSTED_ORIGINS',
    default=[
        'http://localhost:8000',
        'http://127.0.0.1:8000',
        'http://engp.localhost',
    ],
)


DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

LOCAL_APPS = [
    'base',
    'tenants',
    'accounts',
    'onboarding',
    'dashboard',
    'categories',
    'tasks',
    'routines',
    'focus',
    'notes',
    'notifications',
    'ai_agents',
    'reports',
]

INSTALLED_APPS = DJANGO_APPS + LOCAL_APPS

AUTH_USER_MODEL = 'accounts.User'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'tenants.middleware.TenantMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'
ASGI_APPLICATION = 'core.asgi.application'


DATABASE_URL = env('DATABASE_URL', default='')
if DATABASE_URL:
    DATABASES = {'default': env.db('DATABASE_URL')}
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        },
    }


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


LANGUAGE_CODE = env('LANGUAGE_CODE', default='pt-br')
TIME_ZONE = env('TIME_ZONE', default='America/Sao_Paulo')
USE_I18N = True
USE_TZ = True


STATIC_URL = env('STATIC_URL', default='static/')
STATIC_ROOT = Path(env('STATIC_ROOT', default=str(BASE_DIR / 'staticfiles')))
STATICFILES_DIRS = [BASE_DIR / 'static', BASE_DIR / 'design_system']
MEDIA_URL = env('MEDIA_URL', default='media/')
MEDIA_ROOT = Path(env('MEDIA_ROOT', default=str(BASE_DIR / 'media')))

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
EMAIL_BACKEND = env(
    'EMAIL_BACKEND',
    default='django.core.mail.backends.console.EmailBackend',
)
DEFAULT_FROM_EMAIL = env(
    'DEFAULT_FROM_EMAIL',
    default='ENGP <no-reply@localhost>',
)
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'accounts:home'
LOGOUT_REDIRECT_URL = 'accounts:login'


LOG_LEVEL = env('DJANGO_LOG_LEVEL', default='INFO').upper()
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '{asctime} {levelname} {name} {message}',
            'style': '{',
            'datefmt': '%Y-%m-%dT%H:%M:%S%z',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': LOG_LEVEL,
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        'engp': {
            'handlers': ['console'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
    },
}

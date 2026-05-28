import os
from pathlib import Path
import dj_database_url
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

ON_VERCEL = os.environ.get('VERCEL') == '1'

SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'GQLiIuiwRtI3ycxpd8pW-UDr2fBMcb9vQVrcEmrMaujMKif2XohZA3k92hTtPf2ocew'
)
DEBUG = False if ON_VERCEL else (os.environ.get('DEBUG', 'True') == 'True')

_hosts_env = os.environ.get('ALLOWED_HOSTS', '')
ALLOWED_HOSTS = [h.strip() for h in _hosts_env.split(',') if h.strip()] if _hosts_env else ['localhost', '127.0.0.1']
ALLOWED_HOSTS += ['.vercel.app', 'fondeino.com', 'www.fondeino.com']
CSRF_TRUSTED_ORIGINS = ['https://fondeino.com', 'https://www.fondeino.com']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'axes',
    'apps.accounts',
    'apps.credito',
    'apps.nomina',
    'apps.polla',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'axes.middleware.AxesMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.accounts.middleware.ModuloAccesoMiddleware',
    'apps.accounts.middleware.CambioPasswordObligatorioMiddleware',
]

ROOT_URLCONF = 'fondeino_web.urls'

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
                'apps.polla.context_processors.polla_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'fondeino_web.wsgi.application'

DATABASE_URL = os.environ.get('DATABASE_URL', f'sqlite:///{BASE_DIR}/db.sqlite3')
DATABASES = {
    'default': dj_database_url.parse(
        DATABASE_URL,
        conn_max_age=0,          # serverless: cerrar conexión al terminar el request
        conn_health_checks=True,
    )
}

AUTH_USER_MODEL = 'accounts.Usuario'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

# ── Correo electrónico ──
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('EMAIL_HOST_USER', 'noreply@fondeino.com')
EMAIL_CONFIGURADO = bool(EMAIL_HOST_USER)

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── Seguridad de sesión ──
SESSION_COOKIE_AGE      = 1800   # 30 min server-side (respaldo al JS de inactividad)
SESSION_SAVE_EVERY_REQUEST = True  # resetea el timer en cada request
SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # cierra al cerrar el navegador

# ── API Football (api-football.com vía RapidAPI) ──
API_FOOTBALL_KEY = os.environ.get('API_FOOTBALL_KEY', '')

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'

# ── Seguridad HTTP (solo en producción Vercel) ──
SECURE_CONTENT_TYPE_NOSNIFF   = True
SECURE_REFERRER_POLICY        = 'strict-origin-when-cross-origin'
X_FRAME_OPTIONS               = 'DENY'
SESSION_COOKIE_HTTPONLY       = True
CSRF_COOKIE_HTTPONLY          = True
SESSION_COOKIE_SECURE         = ON_VERCEL
CSRF_COOKIE_SECURE            = ON_VERCEL
SECURE_HSTS_SECONDS           = 31536000 if ON_VERCEL else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = ON_VERCEL
SECURE_HSTS_PRELOAD           = ON_VERCEL

# ── django-axes: bloqueo por fuerza bruta ──
AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',
    'django.contrib.auth.backends.ModelBackend',
]
AXES_FAILURE_LIMIT      = 5       # bloquear tras 5 intentos fallidos
AXES_COOLOFF_TIME       = 1       # bloqueo de 1 hora
AXES_RESET_ON_SUCCESS   = True    # reinicia contador al iniciar sesión exitosamente
AXES_LOCKOUT_TEMPLATE   = None    # usa respuesta 403 por defecto
AXES_ENABLE_ADMIN       = True    # ver intentos en /admin/

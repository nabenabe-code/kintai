
from pathlib import Path
import os
import dj_database_url  

# --- プロジェクトのベースパス ---
BASE_DIR = Path(__file__).resolve().parent.parent

# --- セキュリティ／基本フラグ ---
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-me')
DEBUG = os.getenv('DEBUG', 'False').lower() in ('1', 'true', 'yes')

# 許可ホスト：本番ドメインを列挙 
ALLOWED_HOSTS = [h for h in os.getenv('ALLOWED_HOSTS', '127.0.0.1,localhost').split(',') if h]
CSRF_TRUSTED_ORIGINS = [
    o for o in os.getenv('CSRF_TRUSTED_ORIGINS', 'http://127.0.0.1,http://localhost,https://.onrender.com').split(',')
    if o
]

# --- アプリ登録 ---
INSTALLED_APPS = [
    # Django 標準
    'django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes',
    'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles',
    # 勤怠アプリ本体
    'attendance',
]

# --- ミドルウェア ---
# WhiteNoise を SecurityMiddleware の直後に入れる
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', 
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# URL ルートの起点 / WSGI アプリ
ROOT_URLCONF = 'kintai.urls'
WSGI_APPLICATION = 'kintai.wsgi.application'

# --- テンプレート ---
# attendance/templates/attendance/*.html を自動で見つける
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # プロジェクト直下 templates/ を使う場合はここに追加する
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                # テンプレ内で request や user などを参照できるようにする
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# --- データベース --
DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,   # 接続再利用でパフォーマンス改善
        ssl_require=False
    )
}

# --- 静的ファイル（CSS/JS/画像） ---
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
    }
}

# --- 言語／タイムゾーン ---
LANGUAGE_CODE = 'ja'
TIME_ZONE = 'Asia/Tokyo'
USE_I18N = True
USE_TZ = True  # DB はUTC。表示時にローカルへ変換。

# --- 本番セキュリティ強化 ---
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = 'DENY'  # iframe 埋め込み禁止

# --- パスワード強度 ---
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --- 主キー既定 ---
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

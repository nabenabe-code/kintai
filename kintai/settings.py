# kintai/settings.py
from pathlib import Path
import os
import dj_database_url

# -----------------------------
# 基本
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

def getenv_bool(name: str, default: bool) -> bool:
    return str(os.getenv(name, str(int(default)))).lower() in ("1", "true", "yes", "on")

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
DEBUG = getenv_bool("DEBUG", True)  # 本番では環境変数で False に

# 例: ALLOWED_HOSTS="127.0.0.1,localhost,example.onrender.com"
ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "127.0.0.1,localhost").split(",") if h.strip()]

# 例: CSRF_TRUSTED_ORIGINS="http://127.0.0.1,http://localhost,https://*.onrender.com,https://your-domain.example"
CSRF_TRUSTED_ORIGINS = [
    o.strip() for o in os.getenv(
        "CSRF_TRUSTED_ORIGINS",
        "http://127.0.0.1,http://localhost,https://*.onrender.com"
    ).split(",") if o.strip()
]


INSTALLED_APPS = [
    # Django 標準
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # 勤怠アプリ
    "attendance",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # 静的配信（CDNなし想定）
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "kintai.urls"
WSGI_APPLICATION = "kintai.wsgi.application"

# -----------------------------
# テンプレート
# -----------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # プロジェクト直下 templates/ を使う場合はここに追加
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# -----------------------------
# データベース
# -----------------------------
# Render の DATABASE_URL（Postgres）/ ローカルは SQLite
# 本番では接続再利用・SSL を有効化
DB_SSL_REQUIRE = getenv_bool("DB_SSL_REQUIRE", not DEBUG)
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600 if not DEBUG else 0,
        ssl_require=DB_SSL_REQUIRE,
    )
}

# -----------------------------
# 静的/メディア
# -----------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"   # collectstatic の出力
# プロジェクト内に assets を置く場合は追加（任意）
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []

# Django 4.2+ の STORAGES 方式で WhiteNoise を使用
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    }
}

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# -----------------------------
# 国際化
# -----------------------------
LANGUAGE_CODE = "ja"
TIME_ZONE = "Asia/Tokyo"
USE_I18N = True
USE_TZ = True  # DB は UTC、表示時にローカルへ変換

# -----------------------------
# セキュリティ（本番時）
# -----------------------------
if not DEBUG:
    SECURE_SSL_REDIRECT = getenv_bool("SECURE_SSL_REDIRECT", True)
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    # HSTS（CDNやサブドメイン事情に合わせて値調整）
    SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000"))  # 1年
    SECURE_HSTS_INCLUDE_SUBDOMAINS = getenv_bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", True)
    SECURE_HSTS_PRELOAD = getenv_bool("SECURE_HSTS_PRELOAD", False)

# Cookie の扱い
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
CSRF_COOKIE_SAMESITE = os.getenv("CSRF_COOKIE_SAMESITE", "Lax")
X_FRAME_OPTIONS = "DENY"  # iframe 埋め込み禁止

# -----------------------------
# 認証/パスワードポリシー
# -----------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# -----------------------------
# ログ（Render の標準出力に出す）
# -----------------------------
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO" if not DEBUG else "DEBUG")
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {
        "handlers": ["console"],
        "level": LOG_LEVEL,
    },
    "loggers": {
        "django": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
    },
}

# -----------------------------
# メール（開発はコンソール、必要時に本番用へ）
# -----------------------------
EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend" if DEBUG else "django.core.mail.backends.smtp.EmailBackend",
)
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "webmaster@localhost")
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587")) if EMAIL_BACKEND.endswith("smtp.EmailBackend") else 0
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = getenv_bool("EMAIL_USE_TLS", True)
EMAIL_USE_SSL = getenv_bool("EMAIL_USE_SSL", False)

# 任意: 末尾スラッシュ補完
APPEND_SLASH = getenv_bool("APPEND_SLASH", True)

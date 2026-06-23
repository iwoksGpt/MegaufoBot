"""Application configuration for MegaufoBot.

Values are loaded from environment variables / .env so secrets are not committed
into the repository.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Telegram BotFather token
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")

# TMDB API key
TMDB_API_KEY = os.getenv("TMDB_API_KEY", "")
MOVIE_API_PROVIDER = os.getenv("MOVIE_API_PROVIDER", "imdb").lower()

DATABASE_FILE = os.getenv("DATABASE_FILE", "data/movie_bot.db")

# Comma-separated Telegram numeric IDs: ADMIN_IDS=123,456
ADMIN_IDS = [
    int(item.strip())
    for item in os.getenv("ADMIN_IDS", "").split(",")
    if item.strip().isdigit()
]

DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "fa")

WELCOME_MESSAGE = """🎬 به ربات پیشنهاد فیلم و سریال خوش آمدید! 🍿

من می‌توانم به شما در پیدا کردن فیلم‌ها و سریال‌های مورد علاقه‌تان کمک کنم.

از دکمه‌های زیر استفاده کنید یا نام فیلم یا سریال مورد نظر خود را تایپ کنید."""

HELP_MESSAGE = """🔍 *راهنمای ربات پیشنهاد فیلم و سریال*

/start - شروع ربات
/search - جستجوی فیلم یا سریال
/recommend - دریافت پیشنهادات شخصی
/popular - فیلم‌ها و سریال‌های محبوب
/settings - تنظیمات
/help - راهنما

همچنین می‌توانید نام فیلم یا سریال مورد نظر خود را مستقیماً تایپ کنید."""


def validate_config() -> None:
    """Fail fast when required runtime secrets are missing."""
    missing = []
    if not TELEGRAM_TOKEN:
        missing.append("TELEGRAM_TOKEN")
    if MOVIE_API_PROVIDER == "tmdb" and not TMDB_API_KEY:
        missing.append("TMDB_API_KEY")
    if missing:
        joined = ", ".join(missing)
        raise RuntimeError(f"Missing required environment variable(s): {joined}")

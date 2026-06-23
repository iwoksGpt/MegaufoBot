# MegaufoBot

ربات تلگرام پیشنهاد فیلم و سریال با Python، `pyTelegramBotAPI`، دیتابیس SQLite و API سایت TMDB.

## ساختار پروژه

```text
MegaufoBot/
├── main.py                  # لانچر ساده پروژه
├── megaufobot/
│   ├── main.py              # فایل اصلی ربات و handlerها
│   ├── config.py            # تنظیمات و متغیرهای محیطی
│   ├── database.py          # SQLite database layer
│   ├── tmdb_api.py          # ارتباط با TMDB API
│   ├── keyboards.py         # کیبوردها و inline keyboardها
│   ├── messages.py          # متن‌ها و پیام‌های ثابت
│   └── admin_panel.py       # پنل مدیریت
├── data/                    # محل دیتابیس SQLite
├── requirements.txt
└── .env.example
```

## راه‌اندازی

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

سپس داخل `.env` مقدارهای زیر را تنظیم کن:

```env
TELEGRAM_TOKEN=توکن BotFather
TMDB_API_KEY=کلید TMDB
ADMIN_IDS=123456789,987654321
```

## اجرا

```bash
python main.py
```

یا:

```bash
python -m megaufobot.main
```

## قابلیت‌های فعلی

- جستجوی فیلم، سریال و بازیگر
- نمایش جزئیات فیلم و سریال از TMDB
- نمایش پوستر، تریلر، بازیگران و تصاویر
- لیست علاقه‌مندی‌ها
- امتیازدهی کاربر
- پیشنهادات مشابه
- ترندهای روز/هفته
- تنظیمات کاربر
- پنل مدیریت شامل آمار، کاربران و ارسال پیام همگانی

## نکته امنیتی

هیچ توکن یا API Key نباید داخل فایل‌های `.py` کامیت شود. همه کلیدها از `.env` خوانده می‌شوند.

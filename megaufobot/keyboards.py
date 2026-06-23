from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

class Keyboards:
    @staticmethod
    def main_menu():
        markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add(
            KeyboardButton("🔍 جستجو"),
            KeyboardButton("🎬 پیشنهادات"),
            KeyboardButton("🔥 ترندها"),
            KeyboardButton("🌟 محبوب‌ترین‌ها"),
            KeyboardButton("❤️ علاقه‌مندی‌ها"),
            KeyboardButton("⚙️ تنظیمات"),
            KeyboardButton("❓ راهنما")
        )
        return markup
    
    @staticmethod
    def search_type():
        markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add(
            KeyboardButton("🎬 جستجوی فیلم"),
            KeyboardButton("📺 جستجوی سریال"),
            KeyboardButton("👤 جستجوی بازیگر"),
            KeyboardButton("🔍 جستجوی همه موارد"),
            KeyboardButton("🔙 بازگشت")
        )
        return markup
    
    @staticmethod
    def media_details(media_id, media_type, is_favorite=False):
        markup = InlineKeyboardMarkup(row_width=2)
        
        markup.add(
            InlineKeyboardButton("🎭 بازیگران", callback_data=f"cast_{media_type}_{media_id}"),
            InlineKeyboardButton("📊 اطلاعات بیشتر", callback_data=f"more_info_{media_type}_{media_id}"),
            InlineKeyboardButton("📝 نقد و بررسی", callback_data=f"review_{media_type}_{media_id}"),
            InlineKeyboardButton("⭐ امتیازدهی", callback_data=f"rate_{media_type}_{media_id}")
        )
        
        favorite_text = "❤️ حذف از علاقه‌مندی‌ها" if is_favorite else "🤍 افزودن به علاقه‌مندی‌ها"
        favorite_callback = f"unfavorite_{media_type}_{media_id}" if is_favorite else f"favorite_{media_type}_{media_id}"
        
        markup.add(
            InlineKeyboardButton("👍 پیشنهادات مشابه", callback_data=f"similar_{media_type}_{media_id}"),
            InlineKeyboardButton(favorite_text, callback_data=favorite_callback),
            InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_search")
        )
        
        return markup
    
    @staticmethod
    def rating_keyboard(media_id, media_type):
        markup = InlineKeyboardMarkup(row_width=5)
        buttons = []
        
        for i in range(1, 11):
            buttons.append(InlineKeyboardButton(f"{i}", callback_data=f"rate_{media_type}_{media_id}_{i}"))
        
        markup.add(*buttons)
        markup.add(InlineKeyboardButton("🔙 بازگشت", callback_data=f"details_{media_type}_{media_id}"))
        
        return markup
    
    @staticmethod
    def genres_keyboard(genres, media_type):
        markup = InlineKeyboardMarkup(row_width=2)
        buttons = []
        
        for genre in genres:
            buttons.append(InlineKeyboardButton(
                genre['name'], 
                callback_data=f"genre_{media_type}_{genre['id']}"
            ))
        
        markup.add(*buttons)
        markup.add(InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main"))
        
        return markup
    
    @staticmethod
    def pagination(page, total_pages, callback_prefix):
        markup = InlineKeyboardMarkup(row_width=5)
        buttons = []
        
        if page > 1:
            buttons.append(InlineKeyboardButton("⬅️", callback_data=f"{callback_prefix}_{page-1}"))
        
        buttons.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="current_page"))
        
        if page < total_pages:
            buttons.append(InlineKeyboardButton("➡️", callback_data=f"{callback_prefix}_{page+1}"))
        
        markup.add(*buttons)
        markup.add(InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main"))
        
        return markup
    
    @staticmethod
    def pagination_keyboard(page, total_pages, callback_prefix):
        markup = InlineKeyboardMarkup(row_width=5)
        buttons = []
        
        if page > 1:
            buttons.append(InlineKeyboardButton("⬅️", callback_data=f"{callback_prefix}_{page-1}"))
        
        start_page = max(1, page - 2)
        end_page = min(total_pages, start_page + 4)
        
        for p in range(start_page, end_page + 1):
            text = f"• {p} •" if p == page else str(p)
            buttons.append(InlineKeyboardButton(text, callback_data=f"{callback_prefix}_{p}"))
        
        if page < total_pages:
            buttons.append(InlineKeyboardButton("➡️", callback_data=f"{callback_prefix}_{page+1}"))
        
        markup.add(*buttons)
        markup.add(InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main"))
        
        return markup
    
    @staticmethod
    def trends_keyboard():
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("🔥 فیلم‌های ترند امروز", callback_data="trending_movie_day"),
            InlineKeyboardButton("🔥 سریال‌های ترند امروز", callback_data="trending_tv_day"),
            InlineKeyboardButton("📅 فیلم‌های ترند هفته", callback_data="trending_movie_week"),
            InlineKeyboardButton("📅 سریال‌های ترند هفته", callback_data="trending_tv_week"),
            InlineKeyboardButton("🎬 فیلم‌های در حال اکران", callback_data="trending_movie_now_playing"),
            InlineKeyboardButton("📺 سریال‌های در حال پخش", callback_data="trending_tv_on_air"),
            InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")
        )
        return markup
    
    @staticmethod
    def settings_keyboard():
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("🌐 تغییر زبان", callback_data="change_language"),
            InlineKeyboardButton("🎭 ژانرهای مورد علاقه", callback_data="favorite_genres"),
            InlineKeyboardButton("🔄 بروزرسانی خودکار", callback_data="auto_update"),
            InlineKeyboardButton("🔍 جستجوی پیشرفته", callback_data="advanced_search"),
            InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main")
        )
        return markup
        
    @staticmethod
    def favorite_genres_keyboard(selected_genres=None):
        if selected_genres is None:
            selected_genres = []
            
        markup = InlineKeyboardMarkup(row_width=2)
        
        genres = [
            {"id": 28, "name": "اکشن"},
            {"id": 12, "name": "ماجراجویی"},
            {"id": 16, "name": "انیمیشن"},
            {"id": 35, "name": "کمدی"},
            {"id": 80, "name": "جنایی"},
            {"id": 99, "name": "مستند"},
            {"id": 18, "name": "درام"},
            {"id": 10751, "name": "خانوادگی"},
            {"id": 14, "name": "فانتزی"},
            {"id": 36, "name": "تاریخی"},
            {"id": 27, "name": "ترسناک"},
            {"id": 10402, "name": "موزیکال"},
            {"id": 9648, "name": "معمایی"},
            {"id": 10749, "name": "عاشقانه"},
            {"id": 878, "name": "علمی تخیلی"},
            {"id": 10770, "name": "تلویزیونی"},
            {"id": 53, "name": "هیجان‌انگیز"},
            {"id": 10752, "name": "جنگی"},
            {"id": 37, "name": "وسترن"}
        ]
        
        buttons = []
        for genre in genres:
            if genre["id"] in selected_genres:
                buttons.append(InlineKeyboardButton(
                    f"✅ {genre['name']}", 
                    callback_data=f"toggle_genre_{genre['id']}"
                ))
            else:
                buttons.append(InlineKeyboardButton(
                    genre['name'], 
                    callback_data=f"toggle_genre_{genre['id']}"
                ))
        
        markup.add(*buttons)
        markup.add(
            InlineKeyboardButton("💾 ذخیره تغییرات", callback_data="save_genres"),
            InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_settings")
        )
        
        return markup
        
    @staticmethod
    def auto_update_keyboard(status=False):
        markup = InlineKeyboardMarkup(row_width=1)
        
        status_text = "✅ فعال" if status else "❌ غیرفعال"
        toggle_text = "غیرفعال کردن" if status else "فعال کردن"
        
        markup.add(
            InlineKeyboardButton(f"وضعیت فعلی: {status_text}", callback_data="current_status"),
            InlineKeyboardButton(f"🔄 {toggle_text}", callback_data="toggle_auto_update"),
            InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_settings")
        )
        
        return markup
        
    @staticmethod
    def advanced_search_keyboard():
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("🎬 جستجو بر اساس ژانر", callback_data="search_by_genre"),
            InlineKeyboardButton("📅 جستجو بر اساس سال", callback_data="search_by_year"),
            InlineKeyboardButton("⭐ جستجو بر اساس امتیاز", callback_data="search_by_rating"),
            InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_settings")
        )
        
        return markup
    
    @staticmethod
    def language_keyboard():
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("🇮🇷 فارسی", callback_data="lang_fa"),
            InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
            InlineKeyboardButton("🇦🇪 العربية", callback_data="lang_ar"),
            InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_settings")
        )
        return markup
    
    @staticmethod
    def admin_keyboard():
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("📊 آمار", callback_data="admin_stats"),
            InlineKeyboardButton("📢 ارسال پیام همگانی", callback_data="admin_broadcast"),
            InlineKeyboardButton("👥 کاربران", callback_data="admin_users"),
            InlineKeyboardButton("⚙️ تنظیمات ربات", callback_data="admin_settings"),
            InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")
        )
        return markup
        
    @staticmethod
    def favorites_keyboard(page=1, total_pages=1, media_type=None):
        markup = InlineKeyboardMarkup(row_width=2)
        
        filter_buttons = []
        
        all_text = "🎬 همه" if media_type is None else "همه"
        movies_text = "🎬 فیلم‌ها" if media_type == "movie" else "فیلم‌ها"
        tv_text = "📺 سریال‌ها" if media_type == "tv" else "سریال‌ها"
        
        filter_buttons.append(InlineKeyboardButton(all_text, callback_data="favorites_all"))
        filter_buttons.append(InlineKeyboardButton(movies_text, callback_data="favorites_movie"))
        filter_buttons.append(InlineKeyboardButton(tv_text, callback_data="favorites_tv"))
        
        markup.add(*filter_buttons)
        
        pagination_buttons = []
        
        if page > 1:
            pagination_buttons.append(InlineKeyboardButton("⬅️", callback_data=f"favorites_page_{page-1}_{media_type or 'all'}"))
        
        pagination_buttons.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="current_page"))
        
        if page < total_pages:
            pagination_buttons.append(InlineKeyboardButton("➡️", callback_data=f"favorites_page_{page+1}_{media_type or 'all'}"))
        
        markup.add(*pagination_buttons)
        markup.add(InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main"))
        
        return markup
        
    @staticmethod
    def favorite_item_keyboard(media_id, media_type):
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("📋 مشاهده جزئیات", callback_data=f"details_{media_type}_{media_id}"),
            InlineKeyboardButton("❌ حذف از علاقه‌مندی‌ها", callback_data=f"unfavorite_{media_type}_{media_id}"),
            InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_favorites")
        )
        return markup

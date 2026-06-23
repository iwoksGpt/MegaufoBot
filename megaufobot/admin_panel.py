import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from .config import ADMIN_IDS
from .database import Database
from .messages import Messages

class AdminPanel:
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        self.broadcast_messages = {}
    
    def is_admin(self, user_id):
        return user_id in ADMIN_IDS
    
    def show_admin_panel(self, chat_id):
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("📊 آمار", callback_data="admin_stats"),
            InlineKeyboardButton("📢 ارسال پیام همگانی", callback_data="admin_broadcast"),
            InlineKeyboardButton("👥 کاربران", callback_data="admin_users"),
            InlineKeyboardButton("⚙️ تنظیمات ربات", callback_data="admin_settings"),
            InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")
        )
        
        self.bot.send_message(
            chat_id,
            Messages.ADMIN_WELCOME,
            reply_markup=markup
        )
    
    def show_statistics(self, chat_id):
        # دریافت آمار از پایگاه داده
        total_users = self.db.get_total_users()
        stats = self.db.get_statistics(7)
        
        total_searches = sum(stat[1] for stat in stats)
        total_recommendations = sum(stat[2] for stat in stats)
        total_new_users = sum(stat[3] for stat in stats)
        
        # ایجاد پیام آمار
        stats_message = Messages.ADMIN_STATS.format(
            total_users, total_searches, total_recommendations, total_new_users
        )
        
        # ایجاد دکمه بازگشت
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back"))
        
        self.bot.send_message(chat_id, stats_message, reply_markup=markup)
    
    def start_broadcast(self, chat_id):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("❌ لغو", callback_data="admin_cancel_broadcast"))
        
        msg = self.bot.send_message(
            chat_id,
            Messages.ADMIN_BROADCAST_PROMPT,
            reply_markup=markup
        )
        
        self.bot.register_next_step_handler(msg, self.process_broadcast_message)
    
    def process_broadcast_message(self, message):
        # ذخیره پیام برای ارسال همگانی
        self.broadcast_messages[message.chat.id] = message.text
        
        # ایجاد دکمه‌های تأیید و لغو
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("✅ تأیید و ارسال", callback_data="admin_confirm_broadcast"),
            InlineKeyboardButton("❌ لغو", callback_data="admin_cancel_broadcast")
        )
        
        # نمایش پیش‌نمایش پیام
        self.bot.send_message(
            message.chat.id,
            f"📢 پیش‌نمایش پیام:\n\n{message.text}",
            reply_markup=markup
        )
    
    def send_broadcast(self, chat_id):
        if chat_id not in self.broadcast_messages:
            self.bot.send_message(chat_id, "❌ پیامی برای ارسال یافت نشد.")
            return
        
        broadcast_text = self.broadcast_messages[chat_id]
        
        # دریافت لیست تمام کاربران
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT user_id FROM users")
        users = cursor.fetchall()
        
        sent_count = 0
        for user in users:
            try:
                self.bot.send_message(user[0], f"📢 *اطلاعیه مهم*\n\n{broadcast_text}", parse_mode="Markdown")
                sent_count += 1
            except Exception as e:
                print(f"Error sending broadcast to {user[0]}: {e}")
        
        # پاک کردن پیام ذخیره شده
        del self.broadcast_messages[chat_id]
        
        # ارسال گزارش به مدیر
        self.bot.send_message(
            chat_id,
            Messages.ADMIN_BROADCAST_SENT.format(sent_count)
        )
        
        # بازگشت به پنل مدیر
        self.show_admin_panel(chat_id)
    
    def show_users(self, chat_id, page=1, page_size=10):
        # دریافت لیست کاربران با صفحه‌بندی
        cursor = self.db.conn.cursor()
        cursor.execute(
            "SELECT user_id, username, first_name, last_name, join_date FROM users ORDER BY join_date DESC LIMIT ? OFFSET ?",
            (page_size, (page - 1) * page_size)
        )
        users = cursor.fetchall()
        
        # دریافت تعداد کل کاربران
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        total_pages = (total_users + page_size - 1) // page_size
        
        # ایجاد پیام لیست کاربران
        users_message = f"👥 *لیست کاربران* (صفحه {page}/{total_pages}):\n\n"
        
        for i, user in enumerate(users, 1):
            user_id, username, first_name, last_name, join_date = user
            user_name = f"@{username}" if username else f"{first_name} {last_name or ''}".strip()
            users_message += f"{(page - 1) * page_size + i}. {user_name} (ID: {user_id})\n"
        
        # ایجاد دکمه‌های صفحه‌بندی
        markup = InlineKeyboardMarkup(row_width=3)
        buttons = []
        
        if page > 1:
            buttons.append(InlineKeyboardButton("⬅️", callback_data=f"admin_users_{page-1}"))
        
        buttons.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="current_page"))
        
        if page < total_pages:
            buttons.append(InlineKeyboardButton("➡️", callback_data=f"admin_users_{page+1}"))
        
        markup.add(*buttons)
        markup.add(InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back"))
        
        self.bot.send_message(chat_id, users_message, reply_markup=markup, parse_mode="Markdown")
    
    def show_bot_settings(self, chat_id):
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("🛠️ حالت تعمیر و نگهداری", callback_data="admin_maintenance"),
            InlineKeyboardButton("🔄 بروزرسانی پایگاه داده", callback_data="admin_update_db"),
            InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back")
        )
        
        self.bot.send_message(
            chat_id,
            "⚙️ *تنظیمات ربات*\n\nاز دکمه‌های زیر برای مدیریت تنظیمات ربات استفاده کنید.",
            reply_markup=markup,
            parse_mode="Markdown"
        )

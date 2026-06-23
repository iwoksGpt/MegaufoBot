import telebot
import time
import re
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from .config import TELEGRAM_TOKEN, WELCOME_MESSAGE, HELP_MESSAGE, MOVIE_API_PROVIDER, validate_config
from .database import Database
from .tmdb_api import TMDbAPI
from .imdb_api import IMDbAPI
from .keyboards import Keyboards
from .messages import Messages
from .admin_panel import AdminPanel

validate_config()

bot = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode="Markdown")

db = Database()
tmdb = IMDbAPI() if MOVIE_API_PROVIDER == "imdb" else TMDbAPI()
keyboards = Keyboards()
admin_panel = AdminPanel(bot)

user_search_cache = {}
user_states = {}

STATE_SEARCH = "search"
STATE_RATE = "rate"
STATE_SETTINGS = "settings"
STATE_ADMIN = "admin"

@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    
    db.add_user(user_id, username, first_name, last_name)
    db.update_statistics(new_user=1)
    
    bot.send_message(
        message.chat.id,
        WELCOME_MESSAGE,
        reply_markup=keyboards.main_menu()
    )

@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(
        message.chat.id,
        HELP_MESSAGE,
        reply_markup=keyboards.main_menu()
    )

@bot.message_handler(commands=['search'])
def search_command(message):
    user_states[message.from_user.id] = STATE_SEARCH
    bot.send_message(
        message.chat.id,
        Messages.SEARCH_PROMPT,
        reply_markup=keyboards.search_type()
    )

@bot.message_handler(commands=['recommend'])
def recommend_command(message):
    preferences = db.get_preferences(message.from_user.id)
    
    if not any(preferences.values()):
        popular_movies = tmdb.get_popular_movies()
        
        if popular_movies and 'results' in popular_movies:
            results = popular_movies['results'][:5]  
            
            text = Messages.POPULAR_MOVIES + "\n\n"
            for i, movie in enumerate(results, 1):
                title = movie.get('title', 'بدون عنوان')
                year = movie.get('release_date', '')[:4] if movie.get('release_date') else ''
                rating = movie.get('vote_average', 0)
                text += f"{i}. *{title}* ({year}) - ⭐ {rating}/10\n"
            
            markup = InlineKeyboardMarkup(row_width=1)
            for movie in results:
                markup.add(InlineKeyboardButton(
                    f"{movie.get('title', 'بدون عنوان')}",
                    callback_data=f"details_movie_{movie.get('id')}"
                ))
            
            bot.send_message(message.chat.id, text, reply_markup=markup)
        else:
            bot.send_message(message.chat.id, Messages.ERROR)
    else:
        genres = preferences.get('genres', [])
        if genres:
            params = {
                'with_genres': ','.join(map(str, genres)),
                'sort_by': 'popularity.desc'
            }
            recommendations = tmdb.discover_movies(params)
            
            if recommendations and 'results' in recommendations:
                results = recommendations['results'][:5]
                
                text = "🎬 *پیشنهادات شخصی برای شما:*\n\n"
                for i, movie in enumerate(results, 1):
                    title = movie.get('title', 'بدون عنوان')
                    year = movie.get('release_date', '')[:4] if movie.get('release_date') else ''
                    rating = movie.get('vote_average', 0)
                    text += f"{i}. *{title}* ({year}) - ⭐ {rating}/10\n"
                
                markup = InlineKeyboardMarkup(row_width=1)
                for movie in results:
                    markup.add(InlineKeyboardButton(
                        f"{movie.get('title', 'بدون عنوان')}",
                        callback_data=f"details_movie_{movie.get('id')}"
                    ))
                
                bot.send_message(message.chat.id, text, reply_markup=markup)
            else:
                bot.send_message(message.chat.id, Messages.ERROR)
        else:
            popular_movies = tmdb.get_popular_movies()
            
            if popular_movies and 'results' in popular_movies:
                results = popular_movies['results'][:5]
                
                text = Messages.POPULAR_MOVIES + "\n\n"
                for i, movie in enumerate(results, 1):
                    title = movie.get('title', 'بدون عنوان')
                    year = movie.get('release_date', '')[:4] if movie.get('release_date') else ''
                    rating = movie.get('vote_average', 0)
                    text += f"{i}. *{title}* ({year}) - ⭐ {rating}/10\n"
                
                markup = InlineKeyboardMarkup(row_width=1)
                for movie in results:
                    markup.add(InlineKeyboardButton(
                        f"{movie.get('title', 'بدون عنوان')}",
                        callback_data=f"details_movie_{movie.get('id')}"
                    ))
                
                bot.send_message(message.chat.id, text, reply_markup=markup)
            else:
                bot.send_message(message.chat.id, Messages.ERROR)
    
    db.update_statistics(recommendation=1)

@bot.message_handler(commands=['popular'])
def popular_command(message):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🎬 فیلم‌های محبوب", callback_data="popular_movies"),
        InlineKeyboardButton("📺 سریال‌های محبوب", callback_data="popular_tv")
    )
    
    bot.send_message(
        message.chat.id,
        "🌟 چه نوع محتوایی را می‌خواهید مشاهده کنید؟",
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: message.text == "❤️ علاقه‌مندی‌ها")
def favorites_command(message):
    user_id = message.from_user.id
    page = 1
    media_type = None
    
    favorites = db.get_favorites(user_id, media_type)
    total_pages = (len(favorites) + 4) // 5  
    total_pages = max(1, total_pages)  
    
    if not favorites:
        bot.send_message(
            message.chat.id,
            "❌ شما هنوز هیچ فیلم یا سریالی را به لیست علاقه‌مندی‌های خود اضافه نکرده‌اید.",
            reply_markup=keyboards.main_menu()
        )
        return
    
    display_favorites_page(message.chat.id, user_id, page, total_pages, media_type)

def display_favorites_page(chat_id, user_id, page, total_pages, media_type=None):
    favorites = db.get_favorites(user_id, media_type)
    
    start_idx = (page - 1) * 5
    end_idx = min(start_idx + 5, len(favorites))
    page_items = favorites[start_idx:end_idx]
    
    if not page_items:
        bot.send_message(
            chat_id,
            "❌ موردی برای نمایش وجود ندارد.",
            reply_markup=keyboards.main_menu()
        )
        return
    
    text = "❤️ *لیست علاقه‌مندی‌های شما*\n\n"
    
    if media_type == "movie":
        text += "🔍 *فیلتر:* 🎬 فیلم‌ها\n\n"
    elif media_type == "tv":
        text += "🔍 *فیلتر:* 📺 سریال‌ها\n\n"
    else:
        text += "🔍 *فیلتر:* 🎬 همه\n\n"
    
    for i, (media_id, media_type, title, poster_path, added_date) in enumerate(page_items, start_idx + 1):
        media_emoji = "🎬" if media_type == "movie" else "📺"
        text += f"{i}. {media_emoji} *{title}*\n"
    
    markup = InlineKeyboardMarkup(row_width=1)
    
    for media_id, media_type, title, poster_path, added_date in page_items:
        item_text = f"{'🎬' if media_type == 'movie' else '📺'} {title}"
        markup.add(InlineKeyboardButton(item_text, callback_data=f"favorite_item_{media_type}_{media_id}"))
    
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
    
    bot.send_message(
        chat_id,
        text,
        reply_markup=markup,
        parse_mode="Markdown"
    )

def display_favorites_page_callback(chat_id, user_id, page, total_pages, media_type=None, message_id=None):
    favorites = db.get_favorites(user_id, media_type)
    
    start_idx = (page - 1) * 5
    end_idx = min(start_idx + 5, len(favorites))
    page_items = favorites[start_idx:end_idx]
    
    if not page_items:
        bot.edit_message_text(
            "❌ موردی برای نمایش وجود ندارد.",
            chat_id,
            message_id,
            reply_markup=keyboards.favorites_keyboard(page, total_pages, media_type)
        )
        return
    
    text = "❤️ *لیست علاقه‌مندی‌های شما*\n\n"
    
    if media_type == "movie":
        text += "🔍 *فیلتر:* 🎬 فیلم‌ها\n\n"
    elif media_type == "tv":
        text += "🔍 *فیلتر:* 📺 سریال‌ها\n\n"
    else:
        text += "🔍 *فیلتر:* 🎬 همه\n\n"
    
    for i, (media_id, media_type, title, poster_path, added_date) in enumerate(page_items, start_idx + 1):
        media_emoji = "🎬" if media_type == "movie" else "📺"
        text += f"{i}. {media_emoji} *{title}*\n"
    
    markup = InlineKeyboardMarkup(row_width=1)
    
    for media_id, media_type, title, poster_path, added_date in page_items:
        item_text = f"{'🎬' if media_type == 'movie' else '📺'} {title}"
        markup.add(InlineKeyboardButton(item_text, callback_data=f"favorite_item_{media_type}_{media_id}"))
    
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
    
    try:
        bot.edit_message_text(
            text,
            chat_id,
            message_id,
            reply_markup=markup,
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"خطا در نمایش لیست علاقه‌مندی‌ها: {e}")
        try:
            bot.delete_message(chat_id, message_id)
        except:
            pass
            
        bot.send_message(
            chat_id,
            text,
            reply_markup=markup,
            parse_mode="Markdown"
        )

@bot.message_handler(commands=['trends'])
def trends_command(message):
    bot.send_message(
        message.chat.id,
        "🔥 ترندهای فیلم و سریال",
        reply_markup=keyboards.trends_keyboard()
    )

@bot.message_handler(commands=['settings'])
def settings_command(message):
    user_states[message.from_user.id] = STATE_SETTINGS
    bot.send_message(
        message.chat.id,
        Messages.SETTINGS,
        reply_markup=keyboards.settings_keyboard()
    )

@bot.message_handler(commands=['admin'])
def admin_command(message):
    user_id = message.from_user.id
    
    if admin_panel.is_admin(user_id):
        user_states[user_id] = STATE_ADMIN
        admin_panel.show_admin_panel(message.chat.id)
    else:
        bot.send_message(message.chat.id, "❌ شما دسترسی به پنل مدیریت ندارید.")

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    user_id = message.from_user.id
    text = message.text
    
    if text == "🔍 جستجو":
        search_command(message)
    elif text == "🎬 پیشنهادات":
        recommend_command(message)
    elif text == "🔥 ترندها":
        trends_command(message)
    elif text == "🌟 محبوب‌ترین‌ها":
        popular_command(message)
    elif text == "⚙️ تنظیمات":
        settings_command(message)
    elif text == "❓ راهنما":
        help_command(message)
    else:
        if user_id in user_states and user_states[user_id] == STATE_SEARCH:
            search_query(message)
        elif user_id in user_states and user_states[user_id] == STATE_ADMIN:
            pass
        else:
            search_query(message)

def search_query(message):
    query = message.text
    user_id = message.from_user.id
    
    user_search_cache[user_id] = query
    
    results = tmdb.search_multi(query)
    db.update_statistics(search=1)
    
    if results and 'results' in results and results['results']:
        search_results = results['results'][:5]  # 5 نتیجه اول
        
        text = Messages.SEARCH_RESULTS.format(query) + "\n\n"
        markup = InlineKeyboardMarkup(row_width=1)
        
        for item in search_results:
            media_type = item.get('media_type', '')
            
            if media_type == 'movie':
                title = item.get('title', 'بدون عنوان')
                year = item.get('release_date', '')[:4] if item.get('release_date') else ''
                text += f"🎬 *{title}* ({year})\n"
                markup.add(InlineKeyboardButton(
                    f"🎬 {title} ({year})",
                    callback_data=f"details_movie_{item.get('id')}"
                ))
            
            elif media_type == 'tv':
                title = item.get('name', 'بدون عنوان')
                year = item.get('first_air_date', '')[:4] if item.get('first_air_date') else ''
                text += f"📺 *{title}* ({year})\n"
                markup.add(InlineKeyboardButton(
                    f"📺 {title} ({year})",
                    callback_data=f"details_tv_{item.get('id')}"
                ))
            
            elif media_type == 'person':
                name = item.get('name', 'بدون نام')
                text += f"👤 *{name}*\n"
                markup.add(InlineKeyboardButton(
                    f"👤 {name}",
                    callback_data=f"details_person_{item.get('id')}"
                ))
        
        markup.add(InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main"))
        
        bot.send_message(message.chat.id, text, reply_markup=markup)
    else:
        bot.send_message(message.chat.id, Messages.NO_RESULTS)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user_id = call.from_user.id
    data = call.data
    
    if data == "back_to_main":
        if user_id in user_states:
            del user_states[user_id]
        
        bot.edit_message_text(
            "🏠 منوی اصلی",
            call.message.chat.id,
            call.message.message_id
        )
        
        bot.send_message(
            call.message.chat.id,
            "از دکمه‌های زیر استفاده کنید یا نام فیلم یا سریال مورد نظر خود را تایپ کنید.",
            reply_markup=keyboards.main_menu()
        )
    
    elif data == "back_to_search":
        if user_id in user_search_cache:
            query = user_search_cache[user_id]
            results = tmdb.search_multi(query)
            
            if results and 'results' in results and results['results']:
                search_results = results['results'][:5]
                
                text = Messages.SEARCH_RESULTS.format(query) + "\n\n"
                markup = InlineKeyboardMarkup(row_width=1)
                
                for item in search_results:
                    media_type = item.get('media_type', '')
                    
                    if media_type == 'movie':
                        title = item.get('title', 'بدون عنوان')
                        year = item.get('release_date', '')[:4] if item.get('release_date') else ''
                        text += f"🎬 *{title}* ({year})\n"
                        markup.add(InlineKeyboardButton(
                            f"🎬 {title} ({year})",
                            callback_data=f"details_movie_{item.get('id')}"
                        ))
                    
                    elif media_type == 'tv':
                        title = item.get('name', 'بدون عنوان')
                        year = item.get('first_air_date', '')[:4] if item.get('first_air_date') else ''
                        text += f"📺 *{title}* ({year})\n"
                        markup.add(InlineKeyboardButton(
                            f"📺 {title} ({year})",
                            callback_data=f"details_tv_{item.get('id')}"
                        ))
                    
                    elif media_type == 'person':
                        name = item.get('name', 'بدون نام')
                        text += f"👤 *{name}*\n"
                        markup.add(InlineKeyboardButton(
                            f"👤 {name}",
                            callback_data=f"details_person_{item.get('id')}"
                        ))
                
                markup.add(InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main"))
                
                bot.edit_message_text(
                    text,
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=markup
                )
            else:
                bot.answer_callback_query(call.id, "❌ نتایج جستجو در دسترس نیست.")
        else:
            bot.answer_callback_query(call.id, "❌ جستجویی یافت نشد.")
    
    elif data.startswith("search_"):
        search_type = data.split("_")[1]
        user_states[user_id] = STATE_SEARCH
        
        if search_type == "movie":
            bot.edit_message_text(
                "🎬 لطفاً نام فیلم مورد نظر خود را وارد کنید:",
                call.message.chat.id,
                call.message.message_id
            )
        elif search_type == "tv":
            bot.edit_message_text(
                "📺 لطفاً نام سریال مورد نظر خود را وارد کنید:",
                call.message.chat.id,
                call.message.message_id
            )
        elif search_type == "person":
            bot.edit_message_text(
                "👤 لطفاً نام بازیگر یا کارگردان مورد نظر خود را وارد کنید:",
                call.message.chat.id,
                call.message.message_id
            )
        elif search_type == "all":
            bot.edit_message_text(
                "🔍 لطفاً عبارت مورد نظر خود را وارد کنید:",
                call.message.chat.id,
                call.message.message_id
            )
    
    elif data.startswith("details_"):
        parts = data.split("_")
        media_type = parts[1]
        media_id = parts[2]
        
        if media_type == "movie":
            movie = tmdb.get_movie_details(media_id)
            
            if movie:
                title = movie.get('title', 'بدون عنوان')
                original_title = movie.get('original_title', '')
                year = movie.get('release_date', '')[:4] if movie.get('release_date') else ''
                rating = movie.get('vote_average', 0)
                overview = movie.get('overview', 'توضیحاتی موجود نیست.')
                
                genres = ", ".join([g['name'] for g in movie.get('genres', [])])
                
                director = ""
                cast = []
                
                if 'credits' in movie and 'crew' in movie['credits']:
                    directors = [c['name'] for c in movie['credits']['crew'] if c['job'] == 'Director']
                    director = ", ".join(directors)
                
                if 'credits' in movie and 'cast' in movie['credits']:
                    cast = [c['name'] for c in movie['credits']['cast'][:3]]
                
                cast_str = ", ".join(cast)
                
                is_favorite = db.is_favorite(user_id, media_id, media_type)
                
                poster_path = movie.get('poster_path')
                if poster_path:
                    poster_url = tmdb.get_image_url(poster_path)
                    bot.send_photo(
                        call.message.chat.id,
                        poster_url,
                        caption=Messages.MOVIE_DETAILS.format(
                            title, original_title, rating, year, overview, genres, director, cast_str
                        ),
                        reply_markup=keyboards.media_details(media_id, "movie", is_favorite)
                    )
                else:
                    bot.send_message(
                        call.message.chat.id,
                        Messages.MOVIE_DETAILS.format(
                            title, original_title, rating, year, overview, genres, director, cast_str
                        ),
                        reply_markup=keyboards.media_details(media_id, "movie", is_favorite)
                    )
            else:
                bot.answer_callback_query(call.id, "❌ اطلاعات فیلم در دسترس نیست.")
        
        elif media_type == "tv":
            tv = tmdb.get_tv_details(media_id)
            
            if tv:
                title = tv.get('name', 'بدون عنوان')
                original_title = tv.get('original_name', '')
                year = tv.get('first_air_date', '')[:4] if tv.get('first_air_date') else ''
                rating = tv.get('vote_average', 0)
                overview = tv.get('overview', 'توضیحاتی موجود نیست.')
                seasons = tv.get('number_of_seasons', 0)
                
                genres = ", ".join([g['name'] for g in tv.get('genres', [])])
                
                creators = ", ".join([c['name'] for c in tv.get('created_by', [])])
                
                cast = []
                if 'credits' in tv and 'cast' in tv['credits']:
                    cast = [c['name'] for c in tv['credits']['cast'][:3]]
                
                cast_str = ", ".join(cast)
                
                is_favorite = db.is_favorite(user_id, media_id, media_type)
                
                poster_path = tv.get('poster_path')
                if poster_path:
                    poster_url = tmdb.get_image_url(poster_path)
                    bot.send_photo(
                        call.message.chat.id,
                        poster_url,
                        caption=Messages.TV_DETAILS.format(
                            title, original_title, rating, year, overview, genres, creators, cast_str, seasons
                        ),
                        reply_markup=keyboards.media_details(media_id, "tv", is_favorite)
                    )
                else:
                    bot.send_message(
                        call.message.chat.id,
                        Messages.TV_DETAILS.format(
                            title, original_title, rating, year, overview, genres, creators, cast_str, seasons
                        ),
                        reply_markup=keyboards.media_details(media_id, "tv", is_favorite)
                    )
            else:
                bot.answer_callback_query(call.id, "❌ اطلاعات سریال در دسترس نیست.")
        
        elif media_type == "person":
            person = tmdb.get_person_details(media_id)
            
            if person:
                name = person.get('name', 'بدون نام')
                biography = person.get('biography', 'بیوگرافی موجود نیست.')
                birthday = person.get('birthday', 'نامشخص')
                place_of_birth = person.get('place_of_birth', 'نامشخص')
                
                known_for = []
                
                if 'movie_credits' in person and 'cast' in person['movie_credits']:
                    movies = sorted(person['movie_credits']['cast'], key=lambda x: x.get('popularity', 0), reverse=True)[:3]
                    known_for.extend([m.get('title', '') for m in movies])
                
                if 'tv_credits' in person and 'cast' in person['tv_credits']:
                    tv_shows = sorted(person['tv_credits']['cast'], key=lambda x: x.get('popularity', 0), reverse=True)[:3]
                    known_for.extend([t.get('name', '') for t in tv_shows])
                
                known_for_str = ", ".join(known_for[:3])
                
                profile_path = person.get('profile_path')
                if profile_path:
                    profile_url = tmdb.get_image_url(profile_path)
                    bot.send_photo(
                        call.message.chat.id,
                        profile_url,
                        caption=Messages.PERSON_DETAILS.format(
                            name, place_of_birth, birthday, biography, known_for_str
                        )
                    )
                else:
                    bot.send_message(
                        call.message.chat.id,
                        Messages.PERSON_DETAILS.format(
                            name, place_of_birth, birthday, biography, known_for_str
                        )
                    )
            else:
                bot.answer_callback_query(call.id, "❌ اطلاعات شخص در دسترس نیست.")
    
    elif data.startswith("rate_"):
        parts = data.split("_")
        
        if len(parts) == 3:  
            media_type = parts[1]
            media_id = parts[2]
            
            user_states[user_id] = STATE_RATE
            
            title = ""
            if media_type == "movie":
                movie = tmdb.get_movie_details(media_id)
                if movie:
                    title = movie.get('title', 'این فیلم')
            elif media_type == "tv":
                tv = tmdb.get_tv_details(media_id)
                if tv:
                    title = tv.get('name', 'این سریال')
            
            bot.edit_message_reply_markup(
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboards.rating_keyboard(media_id, media_type)
            )
            
            bot.answer_callback_query(call.id, Messages.RATE_PROMPT.format(title))
        
        elif len(parts) == 4:  
            media_type = parts[1]
            media_id = parts[2]
            rating = int(parts[3])
            
            db.add_rating(user_id, media_id, media_type, rating)
            
            title = ""
            if media_type == "movie":
                movie = tmdb.get_movie_details(media_id)
                if movie:
                    title = movie.get('title', 'این فیلم')
            elif media_type == "tv":
                tv = tmdb.get_tv_details(media_id)
                if tv:
                    title = tv.get('name', 'این سریال')
            
            bot.answer_callback_query(call.id, Messages.RATE_SUCCESS.format(rating, title))
            
            bot.edit_message_reply_markup(
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboards.media_details(media_id, media_type)
            )
    
    elif data.startswith("similar_"):
        try:
            parts = data.split("_")
            if len(parts) < 3:  
                bot.answer_callback_query(call.id, "❌ فرمت داده نامعتبر است.")
                return
                
            media_type = parts[1]
            media_id = parts[2]
            
            title = ""
            recommendations = None
            popular_items = None
            
            if media_type == "movie":
                movie = tmdb.get_movie_details(media_id)
                if movie:
                    title = movie.get('title', '')
                recommendations = tmdb.get_movie_recommendations(media_id)
                popular_items = tmdb.get_popular_movies()
            elif media_type == "tv":
                tv = tmdb.get_tv_details(media_id)
                if tv:
                    title = tv.get('name', '')
                recommendations = tmdb.get_tv_recommendations(media_id)
                popular_items = tmdb.get_popular_tv()
            
            results = []
            
            if recommendations and 'results' in recommendations and recommendations['results']:
                rec_count = min(3, len(recommendations['results']))
                if rec_count > 0:
                    results.extend(recommendations['results'][:rec_count])
            
            if popular_items and 'results' in popular_items and popular_items['results']:
                import random
                pop_count = min(2, len(popular_items['results']))
                if pop_count > 0:
                    popular_results = random.sample(popular_items['results'], pop_count)
                    results.extend(popular_results)
            
            if results:
                text = Messages.RECOMMENDATIONS.format(title) + "\n\n"
                markup = InlineKeyboardMarkup(row_width=1)
                
                for item in results:
                    if media_type == "movie":
                        item_title = item.get('title', 'بدون عنوان')
                        year = item.get('release_date', '')[:4] if item.get('release_date') else ''
                        text += f"🎬 *{item_title}* ({year})\n"
                        markup.add(InlineKeyboardButton(
                            f"🎬 {item_title} ({year})",
                            callback_data=f"details_movie_{item.get('id')}"
                        ))
                    elif media_type == "tv":
                        item_title = item.get('name', 'بدون عنوان')
                        year = item.get('first_air_date', '')[:4] if item.get('first_air_date') else ''
                        text += f"📺 *{item_title}* ({year})\n"
                        markup.add(InlineKeyboardButton(
                            f"📺 {item_title} ({year})",
                            callback_data=f"details_tv_{item.get('id')}"
                        ))
                
                markup.add(InlineKeyboardButton("🔙 بازگشت", callback_data=f"details_{media_type}_{media_id}"))
                
                if text.strip():
                    try:
                        bot.edit_message_text(
                            text,
                            call.message.chat.id,
                            call.message.message_id,
                            reply_markup=markup,
                            parse_mode="Markdown"
                        )
                    except Exception as e:
                        print(f"خطا در ویرایش پیام پیشنهادات مشابه: {e}")
                        try:
                            bot.delete_message(call.message.chat.id, call.message.message_id)
                        except:
                            pass
                            
                        bot.send_message(
                            call.message.chat.id,
                            text,
                            reply_markup=markup,
                            parse_mode="Markdown"
                        )
                else:
                    bot.answer_callback_query(call.id, "❌ پیشنهادات مشابه در دسترس نیست.")
            else:
                bot.answer_callback_query(call.id, "❌ پیشنهادات مشابه در دسترس نیست.")
        except Exception as e:
            print(f"خطا در دکمه پیشنهادات مشابه: {e}")
            bot.answer_callback_query(call.id, "❌ خطایی رخ داد. لطفاً دوباره تلاش کنید.")
    
    elif data == "popular_movies":
        try:
            popular = tmdb.get_popular_movies()
            
            if popular and 'results' in popular and popular['results']:
                count = min(10, len(popular['results']))
                if count > 0:
                    results = popular['results'][:count]
                    
                    text = Messages.POPULAR_MOVIES + "\n\n"
                    markup = InlineKeyboardMarkup(row_width=1)
                    
                    for i, movie in enumerate(results, 1):
                        title = movie.get('title', 'بدون عنوان')
                        year = movie.get('release_date', '')[:4] if movie.get('release_date') else ''
                        rating = movie.get('vote_average', 0)
                        text += f"{i}. *{title}* ({year}) - ⭐ {rating}/10\n"
                        markup.add(InlineKeyboardButton(
                            f"{title} ({year})",
                            callback_data=f"details_movie_{movie.get('id')}"
                        ))
                    
                    markup.add(InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main"))
                    
                    try:
                        bot.edit_message_text(
                            text,
                            call.message.chat.id,
                            call.message.message_id,
                            reply_markup=markup,
                            parse_mode="Markdown"
                        )
                    except Exception as e:
                        print(f"خطا در نمایش فیلم‌های محبوب: {e}")
                        try:
                            bot.delete_message(call.message.chat.id, call.message.message_id)
                        except:
                            pass
                            
                        bot.send_message(
                            call.message.chat.id,
                            text,
                            reply_markup=markup,
                            parse_mode="Markdown"
                        )
                else:
                    bot.answer_callback_query(call.id, "❌ اطلاعات فیلم‌های محبوب در دسترس نیست.")
            else:
                bot.answer_callback_query(call.id, "❌ اطلاعات فیلم‌های محبوب در دسترس نیست.")
        except Exception as e:
            print(f"خطا در دکمه فیلم‌های محبوب: {e}")
            bot.answer_callback_query(call.id, "❌ خطایی رخ داد. لطفاً دوباره تلاش کنید.")
    
    elif data == "popular_tv":
        try:
            popular = tmdb.get_popular_tv()
            
            if popular and 'results' in popular and popular['results']:
                count = min(10, len(popular['results']))
                if count > 0:
                    results = popular['results'][:count]
                    
                    text = Messages.POPULAR_TV + "\n\n"
                    markup = InlineKeyboardMarkup(row_width=1)
                    
                    for i, tv in enumerate(results, 1):
                        title = tv.get('name', 'بدون عنوان')
                        year = tv.get('first_air_date', '')[:4] if tv.get('first_air_date') else ''
                        rating = tv.get('vote_average', 0)
                        text += f"{i}. *{title}* ({year}) - ⭐ {rating}/10\n"
                        markup.add(InlineKeyboardButton(
                            f"{title} ({year})",
                            callback_data=f"details_tv_{tv.get('id')}"
                        ))
                    
                    markup.add(InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main"))
                    
                    try:
                        bot.edit_message_text(
                            text,
                            call.message.chat.id,
                            call.message.message_id,
                            reply_markup=markup,
                            parse_mode="Markdown"
                        )
                    except Exception as e:
                        print(f"خطا در نمایش سریال‌های محبوب: {e}")
                        try:
                            bot.delete_message(call.message.chat.id, call.message.message_id)
                        except:
                            pass
                            
                        bot.send_message(
                            call.message.chat.id,
                            text,
                            reply_markup=markup,
                            parse_mode="Markdown"
                        )
                else:
                    bot.answer_callback_query(call.id, "❌ اطلاعات سریال‌های محبوب در دسترس نیست.")
            else:
                bot.answer_callback_query(call.id, "❌ اطلاعات سریال‌های محبوب در دسترس نیست.")
        except Exception as e:
            print(f"خطا در دکمه سریال‌های محبوب: {e}")
            bot.answer_callback_query(call.id, "❌ خطایی رخ داد. لطفاً دوباره تلاش کنید.")
    
    elif data == "change_language":
        bot.edit_message_text(
            "🌐 زبان مورد نظر خود را انتخاب کنید:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboards.language_keyboard()
        )
    
    elif data.startswith("lang_"):
        language = data.split("_")[1]
        db.update_language(user_id, language)
        
        language_name = "فارسی"
        if language == "en":
            language_name = "English"
        elif language == "ar":
            language_name = "العربية"
        
        bot.answer_callback_query(call.id, Messages.LANGUAGE_CHANGED.format(language_name))
        
        bot.edit_message_text(
            Messages.SETTINGS,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboards.settings_keyboard()
        )
    
    elif data == "back_to_settings":
        bot.edit_message_text(
            Messages.SETTINGS,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboards.settings_keyboard()
        )
        
    elif data == "favorite_genres":
        preferences = db.get_preferences(user_id)
        selected_genres = preferences.get('genres', [])
        
        bot.edit_message_text(
            "🎭 ژانرهای مورد علاقه خود را انتخاب کنید:\n\n(ژانرهای انتخاب شده با علامت ✅ مشخص شده‌اند)",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboards.favorite_genres_keyboard(selected_genres)
        )
    
    elif data.startswith("toggle_genre_"):
        genre_id = int(data.split("_")[2])
        
        preferences = db.get_preferences(user_id)
        selected_genres = preferences.get('genres', [])
        
        if genre_id in selected_genres:
            selected_genres.remove(genre_id)
            bot.answer_callback_query(call.id, "❌ ژانر از لیست علاقه‌مندی‌های شما حذف شد.")
        else:
            selected_genres.append(genre_id)
            bot.answer_callback_query(call.id, "✅ ژانر به لیست علاقه‌مندی‌های شما اضافه شد.")
        
        bot.edit_message_reply_markup(
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboards.favorite_genres_keyboard(selected_genres)
        )
    
    elif data == "save_genres":
        preferences = db.get_preferences(user_id)
        selected_genres = preferences.get('genres', [])
        
        db.save_preferences(user_id, genres=selected_genres)
        
        bot.answer_callback_query(call.id, "✅ ژانرهای مورد علاقه شما با موفقیت ذخیره شد.")
        
        bot.edit_message_text(
            Messages.SETTINGS,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboards.settings_keyboard()
        )
    
    elif data == "auto_update":
        preferences = db.get_preferences(user_id)
        auto_update_status = preferences.get('auto_update', False)
        
        bot.edit_message_text(
            "🔄 تنظیمات بروزرسانی خودکار:\n\nبا فعال کردن این گزینه، ربات به صورت خودکار اطلاعات فیلم‌ها و سریال‌های جدید را برای شما ارسال می‌کند.",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboards.auto_update_keyboard(auto_update_status)
        )
    
    elif data == "toggle_auto_update":
        preferences = db.get_preferences(user_id)
        current_status = preferences.get('auto_update', False)
        
        new_status = not current_status
        
        db.save_preferences(user_id, auto_update=new_status)
        
        status_message = "✅ بروزرسانی خودکار فعال شد." if new_status else "❌ بروزرسانی خودکار غیرفعال شد."
        bot.answer_callback_query(call.id, status_message)
        
        bot.edit_message_reply_markup(
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboards.auto_update_keyboard(new_status)
        )
    
    elif data == "current_status":
        bot.answer_callback_query(call.id, "برای تغییر وضعیت، روی دکمه فعال/غیرفعال کردن کلیک کنید.")
    
    elif data == "advanced_search":
        bot.edit_message_text(
            "🔍 جستجوی پیشرفته:\n\nبا استفاده از گزینه‌های زیر می‌توانید جستجوی دقیق‌تری انجام دهید.",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboards.advanced_search_keyboard()
        )
    
    elif data == "search_by_genre":
        genres_data = tmdb.get_genres()
        
        if genres_data and 'genres' in genres_data:
            genres = genres_data['genres']
            
            bot.edit_message_text(
                "🎭 ژانر مورد نظر خود را انتخاب کنید:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboards.genres_keyboard(genres, 'movie')
            )
        else:
            bot.answer_callback_query(call.id, "❌ خطا در دریافت لیست ژانرها. لطفاً دوباره تلاش کنید.")
    
    elif data == "search_by_year":
        bot.answer_callback_query(call.id, "🔜 این قابلیت به زودی اضافه خواهد شد.")
        
        bot.edit_message_text(
            "🔍 جستجوی پیشرفته:\n\nبا استفاده از گزینه‌های زیر می‌توانید جستجوی دقیق‌تری انجام دهید.",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboards.advanced_search_keyboard()
        )
    
    elif data == "search_by_rating":
        bot.answer_callback_query(call.id, "🔜 این قابلیت به زودی اضافه خواهد شد.")
        
        bot.edit_message_text(
            "🔍 جستجوی پیشرفته:\n\nبا استفاده از گزینه‌های زیر می‌توانید جستجوی دقیق‌تری انجام دهید.",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboards.advanced_search_keyboard()
        )
    
    elif data.startswith("admin_"):
        if admin_panel.is_admin(user_id):
            admin_action = data.split("_")[1]
            
            if admin_action == "stats":
                admin_panel.show_statistics(call.message.chat.id)
            elif admin_action == "broadcast":
                admin_panel.start_broadcast(call.message.chat.id)
            elif admin_action == "users":
                admin_panel.show_users(call.message.chat.id)
            elif admin_action == "settings":
                admin_panel.show_bot_settings(call.message.chat.id)
            elif admin_action == "back":
                admin_panel.show_admin_panel(call.message.chat.id)
            elif admin_action == "confirm_broadcast":
                admin_panel.send_broadcast(call.message.chat.id)
            elif admin_action == "cancel_broadcast":
                bot.edit_message_text(
                    "❌ ارسال پیام همگانی لغو شد.",
                    call.message.chat.id,
                    call.message.message_id
                )
                admin_panel.show_admin_panel(call.message.chat.id)
            elif admin_action.startswith("users_"):
                page = int(admin_action.split("_")[1])
                admin_panel.show_users(call.message.chat.id, page)
        else:
            bot.answer_callback_query(call.id, "❌ شما دسترسی به پنل مدیریت ندارید.")
    
    elif data.startswith("favorite_"):
        parts = data.split("_")
        if len(parts) < 3:
            bot.answer_callback_query(call.id, "❌ فرمت داده نامعتبر است.")
            return
            
        media_type = parts[1]
        media_id = parts[2]
        
        title = ""
        poster_path = ""
        if media_type == "movie":
            movie = tmdb.get_movie_details(media_id)
            if movie:
                title = movie.get('title', 'این فیلم')
                poster_path = movie.get('poster_path', '')
        elif media_type == "tv":
            tv = tmdb.get_tv_details(media_id)
            if tv:
                title = tv.get('name', 'این سریال')
                poster_path = tv.get('poster_path', '')
        
        if db.add_to_favorites(user_id, media_id, media_type, title, poster_path):
            bot.answer_callback_query(call.id, f"✅ {title} به لیست علاقه‌مندی‌های شما اضافه شد.")
            
            bot.edit_message_reply_markup(
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboards.media_details(media_id, media_type, True)
            )
        else:
            bot.answer_callback_query(call.id, f"❌ {title} قبلاً به لیست علاقه‌مندی‌های شما اضافه شده است.")
    
    elif data.startswith("unfavorite_"):
        parts = data.split("_")
        if len(parts) < 3:
            bot.answer_callback_query(call.id, "❌ فرمت داده نامعتبر است.")
            return
            
        media_type = parts[1]
        media_id = parts[2]
        
        title = ""
        if media_type == "movie":
            movie = tmdb.get_movie_details(media_id)
            if movie:
                title = movie.get('title', 'این فیلم')
        elif media_type == "tv":
            tv = tmdb.get_tv_details(media_id)
            if tv:
                title = tv.get('name', 'این سریال')
        
        if db.remove_from_favorites(user_id, media_id, media_type):
            bot.answer_callback_query(call.id, f"✅ {title} از لیست علاقه‌مندی‌های شما حذف شد.")
            
            bot.edit_message_reply_markup(
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboards.media_details(media_id, media_type, False)
            )
        else:
            bot.answer_callback_query(call.id, f"❌ {title} در لیست علاقه‌مندی‌های شما وجود ندارد.")
    
    elif data == "favorites_all" or data == "favorites_movie" or data == "favorites_tv":
        media_type = None
        if data == "favorites_movie":
            media_type = "movie"
        elif data == "favorites_tv":
            media_type = "tv"
        
        favorites = db.get_favorites(user_id, media_type)
        total_pages = (len(favorites) + 4) // 5 
        total_pages = max(1, total_pages)  
        
        if not favorites:
            bot.answer_callback_query(call.id, "❌ موردی برای نمایش وجود ندارد.")
            return
        
        display_favorites_page_callback(call.message.chat.id, user_id, 1, total_pages, media_type, call.message.message_id)
        bot.answer_callback_query(call.id)
    
    elif data.startswith("favorites_page_"):
        parts = data.split("_")
        if len(parts) < 4:
            bot.answer_callback_query(call.id, "❌ فرمت داده نامعتبر است.")
            return
        
        page = int(parts[2])
        media_type_str = parts[3]
        media_type = None if media_type_str == "all" else media_type_str
        
        favorites = db.get_favorites(user_id, media_type)
        total_pages = (len(favorites) + 4) // 5 
        total_pages = max(1, total_pages) 
        
        if page < 1 or page > total_pages:
            bot.answer_callback_query(call.id, "❌ صفحه نامعتبر است.")
            return
        
        display_favorites_page_callback(call.message.chat.id, user_id, page, total_pages, media_type, call.message.message_id)
        bot.answer_callback_query(call.id)
    
    elif data == "back_to_favorites":
        favorites = db.get_favorites(user_id)
        total_pages = (len(favorites) + 4) // 5  
        total_pages = max(1, total_pages)  
        
        if not favorites:
            bot.answer_callback_query(call.id, "❌ شما هنوز هیچ فیلم یا سریالی را به علاقه‌مندی‌ها اضافه نکرده‌اید.")
            return
        
        display_favorites_page_callback(call.message.chat.id, user_id, 1, total_pages, None, call.message.message_id)
        bot.answer_callback_query(call.id)
        
    elif data.startswith("favorite_item_"):
        parts = data.split("_")
        if len(parts) < 3:
            bot.answer_callback_query(call.id, "❌ فرمت داده نامعتبر است.")
            return
            
        media_type = parts[2]
        media_id = parts[3]
        
        if media_type == "movie":
            movie = tmdb.get_movie_details(media_id)
            if movie:
                is_favorite = db.is_favorite(user_id, media_id, "movie")
                
                title = movie.get('title', 'بدون عنوان')
                original_title = movie.get('original_title', '')
                year = movie.get('release_date', '')[:4] if movie.get('release_date') else ''
                rating = movie.get('vote_average', 0)
                overview = movie.get('overview', 'توضیحاتی موجود نیست.')
                
                genres = ", ".join([g['name'] for g in movie.get('genres', [])])
                
                director = ""
                cast = []
                
                if 'credits' in movie and 'crew' in movie['credits']:
                    directors = [c['name'] for c in movie['credits']['crew'] if c['job'] == 'Director']
                    director = ", ".join(directors)
                
                if 'credits' in movie and 'cast' in movie['credits']:
                    cast = [c['name'] for c in movie['credits']['cast'][:3]]
                
                cast_str = ", ".join(cast)
                
                poster_path = movie.get('poster_path')
                if poster_path:
                    poster_url = tmdb.get_image_url(poster_path)
                    bot.send_photo(
                        call.message.chat.id,
                        poster_url,
                        caption=Messages.MOVIE_DETAILS.format(
                            title, original_title, rating, year, overview, genres, director, cast_str
                        ),
                        reply_markup=keyboards.media_details(media_id, "movie", is_favorite)
                    )
                else:
                    bot.send_message(
                        call.message.chat.id,
                        Messages.MOVIE_DETAILS.format(
                            title, original_title, rating, year, overview, genres, director, cast_str
                        ),
                        reply_markup=keyboards.media_details(media_id, "movie", is_favorite)
                    )
                bot.answer_callback_query(call.id)
            else:
                bot.answer_callback_query(call.id, "❌ اطلاعات فیلم یافت نشد.")
        
        elif media_type == "tv":
            tv = tmdb.get_tv_details(media_id)
            if tv:
                is_favorite = db.is_favorite(user_id, media_id, "tv")
                
                title = tv.get('name', 'بدون عنوان')
                original_title = tv.get('original_name', '')
                year = tv.get('first_air_date', '')[:4] if tv.get('first_air_date') else ''
                rating = tv.get('vote_average', 0)
                overview = tv.get('overview', 'توضیحاتی موجود نیست.')
                
                genres = ", ".join([g['name'] for g in tv.get('genres', [])])
                
                creators = ", ".join([c['name'] for c in tv.get('created_by', [])])
                
                cast = []
                if 'credits' in tv and 'cast' in tv['credits']:
                    cast = [c['name'] for c in tv['credits']['cast'][:3]]
                
                cast_str = ", ".join(cast)
                
                seasons = tv.get('number_of_seasons', 0)
                
                poster_path = tv.get('poster_path')
                if poster_path:
                    poster_url = tmdb.get_image_url(poster_path)
                    bot.send_photo(
                        call.message.chat.id,
                        poster_url,
                        caption=Messages.TV_DETAILS.format(
                            title, original_title, rating, year, overview, genres, creators, cast_str, seasons
                        ),
                        reply_markup=keyboards.media_details(media_id, "tv", is_favorite)
                    )
                else:
                    bot.send_message(
                        call.message.chat.id,
                        Messages.TV_DETAILS.format(
                            title, original_title, rating, year, overview, genres, creators, cast_str, seasons
                        ),
                        reply_markup=keyboards.media_details(media_id, "tv", is_favorite)
                    )
                bot.answer_callback_query(call.id)
            else:
                bot.answer_callback_query(call.id, "❌ اطلاعات سریال یافت نشد.")
        else:
            bot.answer_callback_query(call.id, "❌ نوع رسانه نامعتبر است.")
    
    elif data.startswith("cast_"):
        try:
            parts = data.split("_")
            if len(parts) < 3:  
                bot.answer_callback_query(call.id, "❌ فرمت داده نامعتبر است.")
                return
                
            media_type = parts[1]
            media_id = parts[2]
            
            if media_type == "movie":
                movie = tmdb.get_movie_details(media_id)
                if movie and 'credits' in movie and 'cast' in movie['credits'] and movie['credits']['cast']:
                    cast = movie['credits']['cast'][:10]  
                    
                    text = f"🎭 *بازیگران {movie.get('title', '')}*\n\n"
                    for actor in cast:
                        name = actor.get('name', '')
                        character = actor.get('character', '')
                        text += f"👤 *{name}* - {character}\n"
                    
                    if text.strip():
                        markup = InlineKeyboardMarkup(row_width=1)
                        markup.add(InlineKeyboardButton("🔙 بازگشت", callback_data=f"details_{media_type}_{media_id}"))
                        
                        try:
                            bot.edit_message_text(
                                text,
                                call.message.chat.id,
                                call.message.message_id,
                                reply_markup=markup,
                                parse_mode="Markdown"
                            )
                        except Exception as e:
                            print(f"خطا در نمایش بازیگران فیلم: {e}")
                            try:
                                bot.delete_message(call.message.chat.id, call.message.message_id)
                            except:
                                pass
                                
                            bot.send_message(
                                call.message.chat.id,
                                text,
                                reply_markup=markup,
                                parse_mode="Markdown"
                            )
                    else:
                        bot.answer_callback_query(call.id, "❌ اطلاعات بازیگران در دسترس نیست.")
                else:
                    bot.answer_callback_query(call.id, "❌ اطلاعات بازیگران در دسترس نیست.")
            
            elif media_type == "tv":
                tv = tmdb.get_tv_details(media_id)
                if tv and 'credits' in tv and 'cast' in tv['credits'] and tv['credits']['cast']:
                    cast = tv['credits']['cast'][:10]  
                    
                    text = f"🎭 *بازیگران {tv.get('name', '')}*\n\n"
                    for actor in cast:
                        name = actor.get('name', '')
                        character = actor.get('character', '')
                        text += f"👤 *{name}* - {character}\n"
                    
                    if text.strip():
                        markup = InlineKeyboardMarkup(row_width=1)
                        markup.add(InlineKeyboardButton("🔙 بازگشت", callback_data=f"details_{media_type}_{media_id}"))
                        
                        try:
                            bot.edit_message_text(
                                text,
                                call.message.chat.id,
                                call.message.message_id,
                                reply_markup=markup,
                                parse_mode="Markdown"
                            )
                        except Exception as e:
                            print(f"خطا در نمایش بازیگران سریال: {e}")
                            try:
                                bot.delete_message(call.message.chat.id, call.message.message_id)
                            except:
                                pass
                                
                            bot.send_message(
                                call.message.chat.id,
                                text,
                                reply_markup=markup,
                                parse_mode="Markdown"
                            )
                    else:
                        bot.answer_callback_query(call.id, "❌ اطلاعات بازیگران در دسترس نیست.")
                else:
                    bot.answer_callback_query(call.id, "❌ اطلاعات بازیگران در دسترس نیست.")
            else:
                bot.answer_callback_query(call.id, "❌ نوع رسانه نامعتبر است.")
        except Exception as e:
            print(f"خطا در دکمه بازیگران: {e}")
            bot.answer_callback_query(call.id, "❌ خطایی رخ داد. لطفاً دوباره تلاش کنید.")
    
    elif data.startswith("trailer_"):
        try:
            parts = data.split("_")
            if len(parts) < 3: 
                bot.answer_callback_query(call.id, "❌ فرمت داده نامعتبر است.")
                return
                
            media_type = parts[1]
            media_id = parts[2]
            
            if media_type == "movie":
                movie = tmdb.get_movie_details(media_id)
                if movie and 'videos' in movie and 'results' in movie['videos']:
                    videos = [v for v in movie['videos']['results'] if v['site'] == 'YouTube']
                    
                    if videos:
                        video = videos[0] 
                        youtube_url = f"https://www.youtube.com/watch?v={video['key']}"
                        
                        text = f"🎥 *ویدیوی {movie.get('title', '')}*\n\n{youtube_url}"
                        
                        if text.strip():
                            markup = InlineKeyboardMarkup(row_width=2)
                            markup.add(
                                InlineKeyboardButton("🎬 مشاهده در یوتیوب", url=youtube_url),
                                InlineKeyboardButton("🔙 بازگشت", callback_data=f"details_{media_type}_{media_id}")
                            )
                            
                            try:
                                bot.edit_message_text(
                                    text,
                                    call.message.chat.id,
                                    call.message.message_id,
                                    reply_markup=markup,
                                    parse_mode="Markdown"
                                )
                            except Exception as e:
                                print(f"خطا در نمایش تریلر فیلم: {e}")
                                try:
                                    bot.delete_message(call.message.chat.id, call.message.message_id)
                                except:
                                    pass
                                    
                                bot.send_message(
                                    call.message.chat.id,
                                    text,
                                    reply_markup=markup,
                                    parse_mode="Markdown"
                                )
                        else:
                            bot.answer_callback_query(call.id, Messages.NO_TRAILER.format("فیلم"))
                    else:
                        bot.answer_callback_query(call.id, Messages.NO_TRAILER.format("فیلم"))
                else:
                    bot.answer_callback_query(call.id, "❌ اطلاعات ویدیو در دسترس نیست.")
            
            elif media_type == "tv":
                tv = tmdb.get_tv_details(media_id)
                if tv and 'videos' in tv and 'results' in tv['videos']:
                    videos = [v for v in tv['videos']['results'] if v['site'] == 'YouTube']
                    
                    if videos:
                        video = videos[0]  
                        youtube_url = f"https://www.youtube.com/watch?v={video['key']}"
                        
                        text = f"🎥 *ویدیوی {tv.get('name', '')}*\n\n{youtube_url}"
                        
                        if text.strip():
                            markup = InlineKeyboardMarkup(row_width=2)
                            markup.add(
                                InlineKeyboardButton("🎬 مشاهده در یوتیوب", url=youtube_url),
                                InlineKeyboardButton("🔙 بازگشت", callback_data=f"details_{media_type}_{media_id}")
                            )
                            
                            try:
                                bot.edit_message_text(
                                    text,
                                    call.message.chat.id,
                                    call.message.message_id,
                                    reply_markup=markup,
                                    parse_mode="Markdown"
                                )
                            except Exception as e:
                                print(f"خطا در نمایش تریلر سریال: {e}")
                                try:
                                    bot.delete_message(call.message.chat.id, call.message.message_id)
                                except:
                                    pass
                                    
                                bot.send_message(
                                    call.message.chat.id,
                                    text,
                                    reply_markup=markup,
                                    parse_mode="Markdown"
                                )
                        else:
                            bot.answer_callback_query(call.id, Messages.NO_TRAILER.format("سریال"))
                    else:
                        bot.answer_callback_query(call.id, Messages.NO_TRAILER.format("سریال"))
                else:
                    bot.answer_callback_query(call.id, "❌ اطلاعات ویدیو در دسترس نیست.")
            else:
                bot.answer_callback_query(call.id, "❌ نوع رسانه نامعتبر است.")
        except Exception as e:
            print(f"خطا در دکمه تریلر: {e}")
            bot.answer_callback_query(call.id, "❌ خطایی رخ داد. لطفاً دوباره تلاش کنید.")
    
    elif data.startswith("backdrops_"):
        parts = data.split("_")
        media_type = parts[1]
        media_id = parts[2]
        
        try:
            if media_type == "movie":
                movie = tmdb.get_movie_details(media_id)
                if movie and 'images' in movie and 'backdrops' in movie['images'] and movie['images']['backdrops']:
                    backdrops = movie['images']['backdrops'][:10] 
                    
                    image = backdrops[0]
                    image_url = tmdb.get_image_url(image['file_path'])
                    
                    text = f"🖼️ *تصاویر پس‌زمینه {movie.get('title', '')}* (1/{len(backdrops)})"
                    
                    markup = InlineKeyboardMarkup(row_width=5)
                    nav_buttons = []
                    
                    if len(backdrops) > 1:
                        for i in range(len(backdrops)):
                            nav_buttons.append(InlineKeyboardButton(f"{i+1}", callback_data=f"backdrop_{media_type}_{media_id}_{i}"))
                    
                    markup.add(*nav_buttons)
                    markup.add(InlineKeyboardButton("🔙 بازگشت", callback_data=f"details_{media_type}_{media_id}"))
                    
                    try:
                        bot.delete_message(call.message.chat.id, call.message.message_id)
                    except:
                        pass
                        
                    bot.send_photo(
                        call.message.chat.id,
                        image_url,
                        caption=text,
                        reply_markup=markup,
                        parse_mode="Markdown"
                    )
                else:
                    bot.answer_callback_query(call.id, "❌ تصویر پس‌زمینه‌ای برای این فیلم یافت نشد.")
            
            elif media_type == "tv":
                tv = tmdb.get_tv_details(media_id)
                if tv and 'images' in tv and 'backdrops' in tv['images'] and tv['images']['backdrops']:
                    backdrops = tv['images']['backdrops'][:10]  
                    
                    image = backdrops[0]
                    image_url = tmdb.get_image_url(image['file_path'])
                    
                    text = f"🖼️ *تصاویر پس‌زمینه {tv.get('name', '')}* (1/{len(backdrops)})"
                    
                    markup = InlineKeyboardMarkup(row_width=5)
                    nav_buttons = []
                    
                    if len(backdrops) > 1:
                        for i in range(len(backdrops)):
                            nav_buttons.append(InlineKeyboardButton(f"{i+1}", callback_data=f"backdrop_{media_type}_{media_id}_{i}"))
                    
                    markup.add(*nav_buttons)
                    markup.add(InlineKeyboardButton("🔙 بازگشت", callback_data=f"details_{media_type}_{media_id}"))
                    
                    try:
                        bot.delete_message(call.message.chat.id, call.message.message_id)
                    except:
                        pass
                        
                    bot.send_photo(
                        call.message.chat.id,
                        image_url,
                        caption=text,
                        reply_markup=markup,
                        parse_mode="Markdown"
                    )
                else:
                    bot.answer_callback_query(call.id, "❌ تصویر پس‌زمینه‌ای برای این سریال یافت نشد.")
            else:
                bot.answer_callback_query(call.id, "❌ نوع رسانه نامعتبر است.")
        except Exception as e:
            print(f"خطا در نمایش تصاویر پس‌زمینه: {e}")
            bot.answer_callback_query(call.id, "❌ خطایی رخ داد. لطفاً دوباره تلاش کنید.")
    
    elif data.startswith("backdrop_"):
        parts = data.split("_")
        media_type = parts[1]
        media_id = parts[2]
        image_index = int(parts[3])
        
        try:
            if media_type == "movie":
                movie = tmdb.get_movie_details(media_id)
                if movie and 'images' in movie and 'backdrops' in movie['images']:
                    backdrops = movie['images']['backdrops'][:10]
                    
                    if 0 <= image_index < len(backdrops):
                        image = backdrops[image_index]
                        image_url = tmdb.get_image_url(image['file_path'])
                        
                        text = f"🖼️ *تصاویر پس‌زمینه {movie.get('title', '')}* ({image_index+1}/{len(backdrops)})"
                        
                        markup = InlineKeyboardMarkup(row_width=5)
                        nav_buttons = []
                        
                        for i in range(len(backdrops)):
                            nav_buttons.append(InlineKeyboardButton(f"{i+1}", callback_data=f"backdrop_{media_type}_{media_id}_{i}"))
                        
                        markup.add(*nav_buttons)
                        markup.add(InlineKeyboardButton("🔙 بازگشت", callback_data=f"details_{media_type}_{media_id}"))
                        
                        bot.edit_message_media(
                            media=telebot.types.InputMediaPhoto(
                                media=image_url,
                                caption=text,
                                parse_mode="Markdown"
                            ),
                            chat_id=call.message.chat.id,
                            message_id=call.message.message_id,
                            reply_markup=markup
                        )
                    else:
                        bot.answer_callback_query(call.id, "❌ شماره تصویر نامعتبر است.")
                else:
                    bot.answer_callback_query(call.id, "❌ اطلاعات تصاویر در دسترس نیست.")
            
            elif media_type == "tv":
                tv = tmdb.get_tv_details(media_id)
                if tv and 'images' in tv and 'backdrops' in tv['images']:
                    backdrops = tv['images']['backdrops'][:10]
                    
                    if 0 <= image_index < len(backdrops):
                        image = backdrops[image_index]
                        image_url = tmdb.get_image_url(image['file_path'])
                        
                        text = f"🖼️ *تصاویر پس‌زمینه {tv.get('name', '')}* ({image_index+1}/{len(backdrops)})"
                        
                        markup = InlineKeyboardMarkup(row_width=5)
                        nav_buttons = []
                        
                        for i in range(len(backdrops)):
                            nav_buttons.append(InlineKeyboardButton(f"{i+1}", callback_data=f"backdrop_{media_type}_{media_id}_{i}"))
                        
                        markup.add(*nav_buttons)
                        markup.add(InlineKeyboardButton("🔙 بازگشت", callback_data=f"details_{media_type}_{media_id}"))
                        
                        bot.edit_message_media(
                            media=telebot.types.InputMediaPhoto(
                                media=image_url,
                                caption=text,
                                parse_mode="Markdown"
                            ),
                            chat_id=call.message.chat.id,
                            message_id=call.message.message_id,
                            reply_markup=markup
                        )
                    else:
                        bot.answer_callback_query(call.id, "❌ شماره تصویر نامعتبر است.")
                else:
                    bot.answer_callback_query(call.id, "❌ اطلاعات تصاویر در دسترس نیست.")
            else:
                bot.answer_callback_query(call.id, "❌ نوع رسانه نامعتبر است.")
        except Exception as e:
            print(f"خطا در ناوبری تصاویر پس‌زمینه: {e}")
            bot.answer_callback_query(call.id, "❌ خطایی رخ داد. لطفاً دوباره تلاش کنید.")
    
    elif data.startswith("images_"):
        parts = data.split("_")
        media_type = parts[1]
        media_id = parts[2]
        
        if media_type == "movie":
            movie = tmdb.get_movie_details(media_id)
            if movie and 'images' in movie:
                images = []
                if 'backdrops' in movie['images'] and movie['images']['backdrops']:
                    images = movie['images']['backdrops'][:5]
                elif 'posters' in movie['images'] and movie['images']['posters']:
                    images = movie['images']['posters'][:5]
                
                if images:
                    image = images[0]
                    image_url = tmdb.get_image_url(image['file_path'])
                    
                    text = f"📸 *تصاویر {movie.get('title', '')}* (1/{len(images)})"
                    
                    markup = InlineKeyboardMarkup(row_width=3)
                    nav_buttons = []
                    
                    if len(images) > 1:
                        for i in range(len(images)):
                            nav_buttons.append(InlineKeyboardButton(f"{i+1}", callback_data=f"image_{media_type}_{media_id}_{i}"))
                    
                    markup.add(*nav_buttons)
                    markup.add(InlineKeyboardButton("🔙 بازگشت", callback_data=f"details_{media_type}_{media_id}"))
                    
                    bot.delete_message(call.message.chat.id, call.message.message_id)
                    bot.send_photo(
                        call.message.chat.id,
                        image_url,
                        caption=text,
                        reply_markup=markup,
                        parse_mode="Markdown"
                    )
                else:
                    bot.answer_callback_query(call.id, "❌ تصویری برای این فیلم یافت نشد.")
            else:
                bot.answer_callback_query(call.id, "❌ اطلاعات تصاویر در دسترس نیست.")
        
        elif media_type == "tv":
            tv = tmdb.get_tv_details(media_id)
            if tv and 'images' in tv:
                images = []
                if 'backdrops' in tv['images'] and tv['images']['backdrops']:
                    images = tv['images']['backdrops'][:5]
                elif 'posters' in tv['images'] and tv['images']['posters']:
                    images = tv['images']['posters'][:5]
                
                if images:
                    image = images[0]
                    image_url = tmdb.get_image_url(image['file_path'])
                    
                    text = f"📸 *تصاویر {tv.get('name', '')}* (1/{len(images)})"
                    
                    markup = InlineKeyboardMarkup(row_width=3)
                    nav_buttons = []
                    
                    if len(images) > 1:
                        for i in range(len(images)):
                            nav_buttons.append(InlineKeyboardButton(f"{i+1}", callback_data=f"image_{media_type}_{media_id}_{i}"))
                    
                    markup.add(*nav_buttons)
                    markup.add(InlineKeyboardButton("🔙 بازگشت", callback_data=f"details_{media_type}_{media_id}"))
                    
                    bot.delete_message(call.message.chat.id, call.message.message_id)
                    bot.send_photo(
                        call.message.chat.id,
                        image_url,
                        caption=text,
                        reply_markup=markup,
                        parse_mode="Markdown"
                    )
                else:
                    bot.answer_callback_query(call.id, "❌ تصویری برای این سریال یافت نشد.")
            else:
                bot.answer_callback_query(call.id, "❌ اطلاعات تصاویر در دسترس نیست.")
    
    elif data.startswith("image_"):
        parts = data.split("_")
        media_type = parts[1]
        media_id = parts[2]
        image_index = int(parts[3])
        
        if media_type == "movie":
            movie = tmdb.get_movie_details(media_id)
            if movie and 'images' in movie:
                images = []
                if 'backdrops' in movie['images'] and movie['images']['backdrops']:
                    images = movie['images']['backdrops'][:5]
                elif 'posters' in movie['images'] and movie['images']['posters']:
                    images = movie['images']['posters'][:5]
                
                if 0 <= image_index < len(images):
                    image = images[image_index]
                    image_url = tmdb.get_image_url(image['file_path'])
                    
                    text = f"📸 *تصاویر {movie.get('title', '')}* ({image_index+1}/{len(images)})"
                    
                    markup = InlineKeyboardMarkup(row_width=3)
                    nav_buttons = []
                    
                    for i in range(len(images)):
                        nav_buttons.append(InlineKeyboardButton(f"{i+1}", callback_data=f"image_{media_type}_{media_id}_{i}"))
                    
                    markup.add(*nav_buttons)
                    markup.add(InlineKeyboardButton("🔙 بازگشت", callback_data=f"details_{media_type}_{media_id}"))
                    
                    try:
                        media = telebot.types.InputMediaPhoto(image_url, caption=text, parse_mode="Markdown")
                        bot.edit_message_media(
                            media=media,
                            chat_id=call.message.chat.id,
                            message_id=call.message.message_id,
                            reply_markup=markup
                        )
                    except Exception as e:
                        bot.delete_message(call.message.chat.id, call.message.message_id)
                        bot.send_photo(
                            call.message.chat.id,
                            image_url,
                            caption=text,
                            reply_markup=markup,
                            parse_mode="Markdown"
                        )
                else:
                    bot.answer_callback_query(call.id, "❌ شماره تصویر نامعتبر است.")
            else:
                bot.answer_callback_query(call.id, "❌ اطلاعات تصاویر در دسترس نیست.")
        
        elif media_type == "tv":
            tv = tmdb.get_tv_details(media_id)
            if tv and 'images' in tv:
                images = []
                if 'backdrops' in tv['images'] and tv['images']['backdrops']:
                    images = tv['images']['backdrops'][:5]
                elif 'posters' in tv['images'] and tv['images']['posters']:
                    images = tv['images']['posters'][:5]
                
                if 0 <= image_index < len(images):
                    image = images[image_index]
                    image_url = tmdb.get_image_url(image['file_path'])
                    
                    text = f"📸 *تصاویر {tv.get('name', '')}* ({image_index+1}/{len(images)})"
                    
                    markup = InlineKeyboardMarkup(row_width=3)
                    nav_buttons = []
                    
                    for i in range(len(images)):
                        nav_buttons.append(InlineKeyboardButton(f"{i+1}", callback_data=f"image_{media_type}_{media_id}_{i}"))
                    
                    markup.add(*nav_buttons)
                    markup.add(InlineKeyboardButton("🔙 بازگشت", callback_data=f"details_{media_type}_{media_id}"))
                    
                    try:
                        media = telebot.types.InputMediaPhoto(image_url, caption=text, parse_mode="Markdown")
                        bot.edit_message_media(
                            media=media,
                            chat_id=call.message.chat.id,
                            message_id=call.message.message_id,
                            reply_markup=markup
                        )
                    except Exception as e:
                        bot.delete_message(call.message.chat.id, call.message.message_id)
                        bot.send_photo(
                            call.message.chat.id,
                            image_url,
                            caption=text,
                            reply_markup=markup,
                            parse_mode="Markdown"
                        )
                else:
                    bot.answer_callback_query(call.id, "❌ شماره تصویر نامعتبر است.")
            else:
                bot.answer_callback_query(call.id, "❌ اطلاعات تصاویر در دسترس نیست.")
    
    elif data.startswith("more_info_"):
        parts = data.split("_")
        media_type = parts[2]
        media_id = parts[3]
        
        if media_type == "movie":
            movie = tmdb.get_movie_details(media_id)
            if movie:
                budget = movie.get('budget', 0)
                revenue = movie.get('revenue', 0)
                runtime = movie.get('runtime', 0)
                status = movie.get('status', '')
                
                text = f"📊 *اطلاعات بیشتر {movie.get('title', '')}*\n\n"
                text += f"⏱️ *مدت زمان:* {runtime} دقیقه\n"
                text += f"💰 *بودجه:* ${budget:,}\n"
                text += f"💵 *فروش:* ${revenue:,}\n"
                text += f"📅 *وضعیت:* {status}\n"
                
                markup = InlineKeyboardMarkup(row_width=1)
                markup.add(InlineKeyboardButton("🔙 بازگشت", callback_data=f"details_{media_type}_{media_id}"))
                
                try:
                    bot.edit_message_text(
                        text,
                        call.message.chat.id,
                        call.message.message_id,
                        reply_markup=markup,
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    try:
                        bot.delete_message(call.message.chat.id, call.message.message_id)
                    except:
                        pass
                    
                    bot.send_message(
                        call.message.chat.id,
                        text,
                        reply_markup=markup,
                        parse_mode="Markdown"
                    )
            else:
                bot.answer_callback_query(call.id, "❌ اطلاعات بیشتر در دسترس نیست.")
        
        elif media_type == "tv":
            tv = tmdb.get_tv_details(media_id)
            if tv:
                status = tv.get('status', '')
                type = tv.get('type', '')
                networks = ", ".join([network.get('name', '') for network in tv.get('networks', [])])
                seasons = tv.get('number_of_seasons', 0)
                episodes = tv.get('number_of_episodes', 0)
                
                text = f"📊 *اطلاعات بیشتر {tv.get('name', '')}*\n\n"
                text += f"📺 *شبکه:* {networks}\n"
                text += f"🎬 *نوع:* {type}\n"
                text += f"📅 *وضعیت:* {status}\n"
                text += f"🔢 *تعداد فصل‌ها:* {seasons}\n"
                text += f"🎬 *تعداد قسمت‌ها:* {episodes}\n"
                
                markup = InlineKeyboardMarkup(row_width=1)
                markup.add(InlineKeyboardButton("🔙 بازگشت", callback_data=f"details_{media_type}_{media_id}"))
                
                try:
                    bot.edit_message_text(
                        text,
                        call.message.chat.id,
                        call.message.message_id,
                        reply_markup=markup,
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    try:
                        bot.delete_message(call.message.chat.id, call.message.message_id)
                    except:
                        pass
                    
                    bot.send_message(
                        call.message.chat.id,
                        text,
                        reply_markup=markup,
                        parse_mode="Markdown"
                    )
            else:
                bot.answer_callback_query(call.id, "❌ اطلاعات بیشتر در دسترس نیست.")
    
    elif data.startswith("download_"):
        try:
            parts = data.split("_")
            if len(parts) < 4:  
                bot.answer_callback_query(call.id, "❌ فرمت داده نامعتبر است.")
                return
                
            media_type = parts[2]
            media_id = parts[3]
            
            if media_type == "movie":
                movie = tmdb.get_movie_details(media_id)
                if movie:
                    title = movie.get('title', '')
                    year = movie.get('release_date', '')[:4] if movie.get('release_date') else ''
                    
                    text = f"📥 *لینک‌های دانلود {title} ({year})*\n\n"
                    text += "🔍 برای دانلود این فیلم می‌توانید از سایت‌های زیر استفاده کنید:\n\n"
                    text += "1. [دیجی موویز](https://digimovie.vip)\n"
                    text += "2. [فیلیمو](https://www.filimo.com)\n"
                    text += "3. [نماوا](https://www.namava.ir)\n"
                    text += "4. [آپارات](https://www.aparat.com)\n\n"
                    text += "⚠️ لطفاً توجه داشته باشید که این ربات لینک مستقیم دانلود ارائه نمی‌دهد و شما باید از سایت‌های رسمی برای دانلود استفاده کنید."
                    
                    markup = InlineKeyboardMarkup(row_width=1)
                    markup.add(InlineKeyboardButton("🔙 بازگشت", callback_data=f"details_{media_type}_{media_id}"))
                    
                    bot.edit_message_text(
                        text,
                        call.message.chat.id,
                        call.message.message_id,
                        reply_markup=markup,
                        parse_mode="Markdown"
                    )
                else:
                    bot.answer_callback_query(call.id, "❌ اطلاعات دانلود در دسترس نیست.")
            
            elif media_type == "tv":
                tv = tmdb.get_tv_details(media_id)
                if tv:
                    title = tv.get('name', '')
                    year = tv.get('first_air_date', '')[:4] if tv.get('first_air_date') else ''
                    
                    text = f"📥 *لینک‌های دانلود {title} ({year})*\n\n"
                    text += "🔍 برای دانلود این سریال می‌توانید از سایت‌های زیر استفاده کنید:\n\n"
                    text += "1. [دیجی موویز](https://digimovie.vip)\n"
                    text += "2. [فیلیمو](https://www.filimo.com)\n"
                    text += "3. [نماوا](https://www.namava.ir)\n"
                    text += "4. [آپارات](https://www.aparat.com)\n\n"
                    text += "⚠️ لطفاً توجه داشته باشید که این ربات لینک مستقیم دانلود ارائه نمی‌دهد و شما باید از سایت‌های رسمی برای دانلود استفاده کنید."
                    
                    markup = InlineKeyboardMarkup(row_width=1)
                    markup.add(InlineKeyboardButton("🔙 بازگشت", callback_data=f"details_{media_type}_{media_id}"))
                    
                    bot.edit_message_text(
                        text,
                        call.message.chat.id,
                        call.message.message_id,
                        reply_markup=markup,
                        parse_mode="Markdown"
                    )
                else:
                    bot.answer_callback_query(call.id, "❌ اطلاعات دانلود در دسترس نیست.")
        except Exception as e:
            print(f"خطا در دکمه دانلود: {e}")
            bot.answer_callback_query(call.id, "❌ خطایی رخ داد. لطفاً دوباره تلاش کنید.")
    elif data.startswith("trending_"):
        try:
            parts = data.split("_")
            if len(parts) < 3:  
                bot.answer_callback_query(call.id, "❌ فرمت داده نامعتبر است.")
                return
                
            media_type = parts[1]  
            time_window = parts[2]  
            
            trending_results = None
            title = ""
            
            if media_type == "movie" and time_window == "day":
                trending_results = tmdb.get_trending_movies_day()
                title = "🔥 فیلم‌های ترند امروز"
            elif media_type == "tv" and time_window == "day":
                trending_results = tmdb.get_trending_tv_day()
                title = "🔥 سریال‌های ترند امروز"
            elif media_type == "movie" and time_window == "week":
                trending_results = tmdb.get_trending_movies_week()
                title = "📅 فیلم‌های ترند هفته"
            elif media_type == "tv" and time_window == "week":
                trending_results = tmdb.get_trending_tv_week()
                title = "📅 سریال‌های ترند هفته"
            elif media_type == "movie" and time_window == "now_playing":
                trending_results = tmdb.get_now_playing_movies()
                title = "🎬 فیلم‌های در حال اکران"
            elif media_type == "tv" and time_window == "on_air":
                trending_results = tmdb.get_on_the_air_tv()
                title = "📺 سریال‌های در حال پخش"
            
            if trending_results and 'results' in trending_results and trending_results['results']:
                count = min(10, len(trending_results['results']))
                if count > 0:
                    results = trending_results['results'][:count]
                    
                    text = f"*{title}*\n\n"
                    markup = InlineKeyboardMarkup(row_width=1)
                    
                    for i, item in enumerate(results, 1):
                        if media_type == "movie":
                            item_title = item.get('title', 'بدون عنوان')
                            year = item.get('release_date', '')[:4] if item.get('release_date') else ''
                            rating = item.get('vote_average', 0)
                            text += f"{i}. *{item_title}* ({year}) - ⭐ {rating}/10\n"
                            markup.add(InlineKeyboardButton(
                                f"{item_title} ({year})",
                                callback_data=f"details_movie_{item.get('id')}"
                            ))
                        elif media_type == "tv":
                            item_title = item.get('name', 'بدون عنوان')
                            year = item.get('first_air_date', '')[:4] if item.get('first_air_date') else ''
                            rating = item.get('vote_average', 0)
                            text += f"{i}. *{item_title}* ({year}) - ⭐ {rating}/10\n"
                            markup.add(InlineKeyboardButton(
                                f"{item_title} ({year})",
                                callback_data=f"details_tv_{item.get('id')}"
                            ))
                    
                    markup.add(InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main"))
                    
                    try:
                        bot.edit_message_text(
                            text,
                            call.message.chat.id,
                            call.message.message_id,
                            reply_markup=markup,
                            parse_mode="Markdown"
                        )
                    except Exception as e:
                        print(f"خطا در نمایش {title}: {e}")
                        try:
                            bot.delete_message(call.message.chat.id, call.message.message_id)
                        except:
                            pass
                            
                        bot.send_message(
                            call.message.chat.id,
                            text,
                            reply_markup=markup,
                            parse_mode="Markdown"
                        )
                else:
                    bot.answer_callback_query(call.id, f"❌ اطلاعات {title} در دسترس نیست.")
            else:
                bot.answer_callback_query(call.id, f"❌ اطلاعات {title} در دسترس نیست.")
        except Exception as e:
            print(f"خطا در دکمه ترندها: {e}")
            bot.answer_callback_query(call.id, "❌ خطایی رخ داد. لطفاً دوباره تلاش کنید.")
    elif data.startswith("review_"):
        try:
            parts = data.split("_")
            if len(parts) < 3:  
                bot.answer_callback_query(call.id, "❌ فرمت داده نامعتبر است.")
                return
                
            media_type = parts[1]  
            media_id = parts[2]
            page = 1
            if len(parts) >= 4 and parts[3].isdigit():
                page = int(parts[3])
            
            reviews = None
            title = ""
            
            if media_type == "movie":
                movie = tmdb.get_movie_details(media_id)
                reviews = tmdb.get_movie_reviews(media_id, page)
                title = movie.get('title', 'فیلم')
            elif media_type == "tv":
                tv = tmdb.get_tv_details(media_id)
                reviews = tmdb.get_tv_reviews(media_id, page)
                title = tv.get('name', 'سریال')
            
            if reviews and 'results' in reviews and reviews['results']:
                results = reviews['results']
                total_pages = reviews.get('total_pages', 1)
                
                text = f"📝 *نقد و بررسی {title}*\n\n"
                
                for i, review in enumerate(results, 1):
                    author = review.get('author', 'ناشناس')
                    content = review.get('content', '')
                    if len(content) > 300:
                        content = content[:297] + '...'
                    
                    text += f"👤 *{author}*:\n{content}\n\n"
                
                markup = InlineKeyboardMarkup(row_width=5)
                pagination_buttons = []
                
                if page > 1:
                    pagination_buttons.append(InlineKeyboardButton("⬅️", callback_data=f"review_{media_type}_{media_id}_{page-1}"))
                
                pagination_buttons.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="current_page"))
                
                if page < total_pages:
                    pagination_buttons.append(InlineKeyboardButton("➡️", callback_data=f"review_{media_type}_{media_id}_{page+1}"))
                
                markup.add(*pagination_buttons)
                markup.add(InlineKeyboardButton("🔙 بازگشت", callback_data=f"details_{media_type}_{media_id}"))
                
                try:
                    bot.edit_message_text(
                        text,
                        call.message.chat.id,
                        call.message.message_id,
                        reply_markup=markup,
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    print(f"خطا در نمایش نقد و بررسی: {e}")
                    try:
                        bot.delete_message(call.message.chat.id, call.message.message_id)
                    except:
                        pass
                        
                    bot.send_message(
                        call.message.chat.id,
                        text,
                        reply_markup=markup,
                        parse_mode="Markdown"
                    )
            else:
                bot.answer_callback_query(call.id, f"❌ نقد و بررسی برای {title} در دسترس نیست.")
        except Exception as e:
            print(f"خطا در دکمه نقد و بررسی: {e}")
            bot.answer_callback_query(call.id, "❌ خطایی رخ داد. لطفاً دوباره تلاش کنید.")
    else:
        bot.answer_callback_query(call.id, "⚠️ این قابلیت هنوز پیاده‌سازی نشده است.")

if __name__ == "__main__":
    print("ربات پیشنهاد فیلم و سریال در حال اجرا است...")
    retry_count = 0
    max_retries = 5
    retry_delay = 10
    
    while True:
        try:
            bot.polling(none_stop=True)
            break  
        except Exception as e:
            retry_count += 1
            print(f"خطا: {e}")
            
            if retry_count > max_retries:
                print(f"پس از {max_retries} تلاش ناموفق، ربات متوقف شد.")
                break
                
            print(f"تلاش مجدد برای اتصال ({retry_count}/{max_retries}) پس از {retry_delay} ثانیه...")
            time.sleep(retry_delay)

            retry_delay = min(retry_delay * 2, 60)

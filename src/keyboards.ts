import { keyboard } from './telegram';
import type { Lang } from './messages';

export function mainMenu(lang: Lang = 'fa') {
  const en = lang === 'en';
  return keyboard([
    [{ text: en ? '🔍 Search' : '🔍 جستجو', callback_data: 'action_search' }, { text: en ? '🌟 Popular' : '🌟 محبوب‌ترین‌ها', callback_data: 'popular_menu' }],
    [{ text: en ? '👤 Profile' : '👤 پروفایل', callback_data: 'profile' }, { text: en ? '❤️ Favorites' : '❤️ علاقه‌مندی‌ها', callback_data: 'favorites' }],
    [{ text: en ? '❓ Help' : '❓ راهنما', callback_data: 'help' }]
  ]);
}

export function popularMenu(lang: Lang = 'fa') {
  const en = lang === 'en';
  return keyboard([
    [{ text: en ? '🎬 Popular Movies' : '🎬 فیلم‌های محبوب', callback_data: 'popular_movie' }, { text: en ? '📺 Popular TV' : '📺 سریال‌های محبوب', callback_data: 'popular_tv' }],
    [{ text: en ? '🔙 Back' : '🔙 بازگشت', callback_data: 'home' }]
  ]);
}

export function titleActions(id: string, type: 'movie' | 'tv', favorite: boolean, lang: Lang = 'fa') {
  const en = lang === 'en';
  return keyboard([
    [{ text: favorite ? (en ? '💔 Glass Remove Favorite' : '💔 حذف از علاقه‌مندی') : (en ? '💎 Glass Add Favorite' : '💎 افزودن شیشه‌ای به علاقه‌مندی'), callback_data: `${favorite ? 'unfav' : 'fav'}_${id}` }],
    [{ text: en ? '⭐ Rate 1–10' : '⭐ امتیازدهی ۱ تا ۱۰', callback_data: `rate_${type}_${id}` }, { text: en ? '🎭 Cast' : '🎭 بازیگران', callback_data: `credits_${id}` }],
    [{ text: en ? '🔙 Back Home' : '🔙 بازگشت به خانه', callback_data: 'home' }]
  ]);
}

export function ratingKeyboard(id: string, type: string, lang: Lang = 'fa') {
  const rows = [];
  for (let start = 1; start <= 10; start += 5) {
    rows.push(Array.from({ length: 5 }, (_, index) => {
      const score = start + index;
      return { text: `⭐ ${score}`, callback_data: `rated_${type}_${id}_${score}` };
    }));
  }
  rows.push([{ text: lang === 'en' ? '🔙 Back' : '🔙 بازگشت', callback_data: `details_${type}_${id}` }]);
  return keyboard(rows);
}

export function profileKeyboard(lang: Lang = 'fa') {
  const en = lang === 'en';
  return keyboard([
    [{ text: en ? '🇮🇷 Persian' : '🇮🇷 فارسی', callback_data: 'lang_fa' }, { text: en ? '🇬🇧 English' : '🇬🇧 انگلیسی', callback_data: 'lang_en' }],
    [{ text: en ? '❤️ My Favorites' : '❤️ علاقه‌مندی‌های من', callback_data: 'favorites' }, { text: en ? '🏠 Home' : '🏠 خانه', callback_data: 'home' }]
  ]);
}

export function adminMenu() {
  return keyboard([
    [{ text: '📊 آمار زنده', callback_data: 'admin_stats' }, { text: '👥 کاربران', callback_data: 'admin_users_0' }],
    [{ text: '📢 ارسال همگانی', callback_data: 'admin_broadcast' }, { text: '🔎 لاگ جستجوها', callback_data: 'admin_logs' }],
    [{ text: '🏠 خروج از پنل', callback_data: 'home' }]
  ]);
}

export function adminUserActions(userId: number, blocked: boolean) {
  return keyboard([
    [{ text: blocked ? '✅ آزاد کردن کاربر' : '⛔️ مسدود کردن کاربر', callback_data: `${blocked ? 'admin_unblock' : 'admin_block'}_${userId}` }],
    [{ text: '❤️ علاقه‌مندی‌های کاربر', callback_data: `admin_user_favs_${userId}` }],
    [{ text: '🔙 لیست کاربران', callback_data: 'admin_users_0' }, { text: '👑 پنل مدیریت', callback_data: 'admin_home' }]
  ]);
}

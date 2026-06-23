export type Lang = 'fa' | 'en';

const dict = {
  fa: {
    welcome: `🎬 *به MegaufoBot خوش آمدی* 🍿\n\nمن با Free IMDb API فیلم‌ها و سریال‌ها را جستجو می‌کنم، جزئیات کامل می‌دهم، علاقه‌مندی‌ها و امتیازهای تو را ذخیره می‌کنم.\n\nاسم فیلم/سریال را فارسی یا انگلیسی بفرست.`,
    help: `🔍 *راهنما*\n\n/start - شروع\n/profile - پروفایل\n/favorites - علاقه‌مندی‌ها\n/popular - محبوب‌ها\n/admin - پنل مدیریت\n\nمثال جستجو: تلقین، Interstellar، برکینگ بد`,
    searchPrompt: '🔎 اسم فیلم یا سریال را فارسی یا انگلیسی بفرست.',
    noResults: '❌ نتیجه‌ای پیدا نشد. عبارت دیگری را امتحان کن.',
    favoritesEmpty: '❤️ هنوز چیزی به علاقه‌مندی‌ها اضافه نکردی.',
    blocked: '⛔️ دسترسی شما به ربات محدود شده است.',
    adminDenied: '❌ دسترسی مدیریت نداری.',
    choosePopular: '🌟 چه چیزی را می‌خواهی ببینی؟',
    profileTitle: '👤 پروفایل شما',
    languageUpdated: '✅ زبان ربات برای شما تغییر کرد.',
    adminTitle: '👑 پنل مدیریت قدرتمند MegaufoBot',
    broadcastPrompt: '📢 متن پیام همگانی را بفرست. برای لغو بنویس: لغو',
    broadcastCanceled: '❌ ارسال همگانی لغو شد.',
    broadcastDone: '✅ پیام همگانی ارسال شد.'
  },
  en: {
    welcome: `🎬 *Welcome to MegaufoBot* 🍿\n\nI search movies and TV shows using the free IMDb API, show rich details, and save your favorites/ratings.\n\nSend a movie or TV title in English or Persian.`,
    help: `🔍 *Help*\n\n/start - Start\n/profile - Profile\n/favorites - Favorites\n/popular - Popular\n/admin - Admin panel\n\nSearch examples: Inception, Interstellar, Breaking Bad`,
    searchPrompt: '🔎 Send a movie or TV show title in English or Persian.',
    noResults: '❌ No results found. Try another query.',
    favoritesEmpty: '❤️ You have no favorites yet.',
    blocked: '⛔️ Your access to this bot is restricted.',
    adminDenied: '❌ You do not have admin access.',
    choosePopular: '🌟 What do you want to see?',
    profileTitle: '👤 Your profile',
    languageUpdated: '✅ Your bot language has been updated.',
    adminTitle: '👑 MegaufoBot Power Admin Panel',
    broadcastPrompt: '📢 Send the broadcast text. Type cancel to abort.',
    broadcastCanceled: '❌ Broadcast canceled.',
    broadcastDone: '✅ Broadcast sent.'
  }
} satisfies Record<Lang, Record<string, string>>;

export function t(lang: Lang | string | undefined, key: keyof typeof dict.fa): string {
  const safeLang: Lang = lang === 'en' ? 'en' : 'fa';
  return dict[safeLang][key];
}

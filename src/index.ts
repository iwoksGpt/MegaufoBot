import type { Env, TelegramCallbackQuery, TelegramMessage, TelegramUpdate, ImdbTitle } from './types';
import { TelegramAPI } from './telegram';
import { HELP, WELCOME } from './messages';
import { adminMenu, mainMenu, popularMenu, ratingKeyboard, titleActions } from './keyboards';
import { displayTitle, getTitle, image, listCredits, listPopular, mediaType, rating, searchTitles, year } from './imdb';
import { addFavorite, addUser, incrementStats, isFavorite, listFavorites, removeFavorite, saveRating, stats } from './db';

function isAdmin(env: Env, userId?: number): boolean {
  if (!userId) return false;
  return (env.ADMIN_IDS ?? '').split(',').map((id) => id.trim()).includes(String(userId));
}

function escapeMd(text: string): string {
  return text.replace(/([_*`\[])/g, '\\$1');
}

function describeTitle(title: ImdbTitle): string {
  const name = escapeMd(displayTitle(title));
  const genres = title.genres?.length ? title.genres.join('، ') : 'نامشخص';
  const plot = title.plot || title.description || 'توضیحاتی موجود نیست.';
  return `*${name}*\n${mediaType(title) === 'movie' ? '🎬 فیلم' : '📺 سریال'} | 🗓 ${year(title)} | ⭐ ${rating(title)}\n\n🎭 *ژانر:* ${escapeMd(genres)}\n\n📝 ${escapeMd(plot).slice(0, 1200)}`;
}

async function showTitle(env: Env, tg: TelegramAPI, chatId: number, userId: number, id: string, editMessageId?: number) {
  const title = await getTitle(id);
  if (!title) {
    await tg.sendMessage(chatId, '❌ اطلاعات این عنوان پیدا نشد.', mainMenu());
    return;
  }
  await incrementStats(env, 'details');
  const fav = await isFavorite(env, userId, id);
  const text = describeTitle(title);
  const markup = titleActions(id, mediaType(title), fav);
  const poster = image(title);
  if (editMessageId) {
    await tg.editMessageText(chatId, editMessageId, text, markup).catch(() => tg.sendMessage(chatId, text, markup));
  } else if (poster) {
    await tg.sendPhoto(chatId, poster, text, markup).catch(() => tg.sendMessage(chatId, text, markup));
  } else {
    await tg.sendMessage(chatId, text, markup);
  }
}

async function handleSearch(env: Env, tg: TelegramAPI, message: TelegramMessage, query: string) {
  await incrementStats(env, 'searches');
  const results = await searchTitles(query, 8);
  if (!results.length) {
    await tg.sendMessage(message.chat.id, '❌ نتیجه‌ای پیدا نشد. عبارت دیگری را امتحان کن.', mainMenu());
    return;
  }
  const rows = results.map((title) => [{
    text: `${mediaType(title) === 'movie' ? '🎬' : '📺'} ${displayTitle(title)} (${year(title)})`,
    callback_data: `details_${mediaType(title)}_${title.id}`
  }]);
  rows.push([{ text: '🔙 بازگشت', callback_data: 'home' }]);
  await tg.sendMessage(message.chat.id, `🔍 نتایج برای *${escapeMd(query)}*:`, { inline_keyboard: rows });
}

async function handleMessage(env: Env, tg: TelegramAPI, message: TelegramMessage) {
  await addUser(env, message.from);
  const text = (message.text ?? '').trim();
  if (!text) return;
  if (text === '/start') return tg.sendMessage(message.chat.id, WELCOME, mainMenu());
  if (text === '/help') return tg.sendMessage(message.chat.id, HELP, mainMenu());
  if (text === '/popular') return tg.sendMessage(message.chat.id, '🌟 چه چیزی را می‌خواهی ببینی؟', popularMenu());
  if (text === '/favorites') return showFavorites(env, tg, message.chat.id, message.from?.id ?? 0);
  if (text === '/admin') {
    if (!isAdmin(env, message.from?.id)) return tg.sendMessage(message.chat.id, '❌ دسترسی مدیریت نداری.');
    return tg.sendMessage(message.chat.id, '👑 پنل مدیریت MegaufoBot', adminMenu());
  }
  await handleSearch(env, tg, message, text.replace(/^\/search\s*/i, ''));
}

async function showFavorites(env: Env, tg: TelegramAPI, chatId: number, userId: number) {
  const rows = await listFavorites(env, userId);
  if (!rows.length) return tg.sendMessage(chatId, '❤️ هنوز چیزی به علاقه‌مندی‌ها اضافه نکردی.', mainMenu());
  const buttons = rows.map((row: Record<string, unknown>) => [{
    text: `${row.media_type === 'movie' ? '🎬' : '📺'} ${row.title}`,
    callback_data: `details_${row.media_type}_${row.title_id}`
  }]);
  buttons.push([{ text: '🔙 بازگشت', callback_data: 'home' }]);
  return tg.sendMessage(chatId, '❤️ *علاقه‌مندی‌های شما*', { inline_keyboard: buttons });
}

async function handleCallback(env: Env, tg: TelegramAPI, callback: TelegramCallbackQuery) {
  await addUser(env, callback.from);
  const data = callback.data ?? '';
  const chatId = callback.message?.chat.id;
  const messageId = callback.message?.message_id;
  await tg.answerCallbackQuery(callback.id).catch(() => undefined);
  if (!chatId) return;

  if (data === 'home') return tg.sendMessage(chatId, WELCOME, mainMenu());
  if (data === 'help') return tg.sendMessage(chatId, HELP, mainMenu());
  if (data === 'action_search') return tg.sendMessage(chatId, '🔍 نام فیلم یا سریال را تایپ کن.');
  if (data === 'popular_menu') return tg.sendMessage(chatId, '🌟 چه چیزی را می‌خواهی ببینی؟', popularMenu());
  if (data === 'favorites') return showFavorites(env, tg, chatId, callback.from.id);
  if (data === 'admin_stats') {
    if (!isAdmin(env, callback.from.id)) return tg.sendMessage(chatId, '❌ دسترسی مدیریت نداری.');
    const s = await stats(env);
    return tg.sendMessage(chatId, `📊 *آمار ۷ روز اخیر*\n\n👥 کل کاربران: ${s.totalUsers}\n🔍 جستجوها: ${s.searches}\n📄 جزئیات: ${s.details}\n❤️ علاقه‌مندی‌ها: ${s.favorites}\n🆕 کاربران جدید: ${s.new_users}`, adminMenu());
  }

  if (data === 'popular_movie' || data === 'popular_tv') {
    const titles = await listPopular(data === 'popular_movie' ? 'MOVIE' : 'TV_SERIES');
    const buttons = titles.map((title) => [{
      text: `${mediaType(title) === 'movie' ? '🎬' : '📺'} ${displayTitle(title)} (${year(title)})`,
      callback_data: `details_${mediaType(title)}_${title.id}`
    }]);
    buttons.push([{ text: '🔙 بازگشت', callback_data: 'home' }]);
    return tg.sendMessage(chatId, data === 'popular_movie' ? '🎬 *فیلم‌های محبوب*' : '📺 *سریال‌های محبوب*', { inline_keyboard: buttons });
  }

  if (data.startsWith('details_')) {
    const [, , id] = data.split('_');
    return showTitle(env, tg, chatId, callback.from.id, id, messageId);
  }

  if (data.startsWith('fav_')) {
    const id = data.slice(4);
    const title = await getTitle(id);
    if (!title) return tg.sendMessage(chatId, '❌ عنوان پیدا نشد.');
    await addFavorite(env, callback.from.id, title);
    return showTitle(env, tg, chatId, callback.from.id, id, messageId);
  }

  if (data.startsWith('unfav_')) {
    const id = data.slice(6);
    await removeFavorite(env, callback.from.id, id);
    return showTitle(env, tg, chatId, callback.from.id, id, messageId);
  }

  if (data.startsWith('rate_')) {
    const [, type, id] = data.split('_');
    return tg.editMessageText(chatId, messageId!, '⭐ از ۱ تا ۱۰ چه امتیازی می‌دهی؟', ratingKeyboard(id, type));
  }

  if (data.startsWith('rated_')) {
    const [, type, id, score] = data.split('_');
    await saveRating(env, callback.from.id, id, type, Number(score));
    await tg.sendMessage(chatId, `✅ امتیاز ${score}/10 ثبت شد.`);
    return showTitle(env, tg, chatId, callback.from.id, id, messageId);
  }

  if (data.startsWith('credits_')) {
    const id = data.slice(8);
    const names = await listCredits(id);
    return tg.sendMessage(chatId, names.length ? `🎭 *بازیگران/عوامل*\n\n${names.map(escapeMd).join('\n')}` : '❌ اطلاعات بازیگران در دسترس نیست.', mainMenu());
  }

  return tg.sendMessage(chatId, '⚠️ این گزینه هنوز پشتیبانی نمی‌شود.', mainMenu());
}

async function handleUpdate(env: Env, update: TelegramUpdate) {
  const tg = new TelegramAPI(env.TELEGRAM_TOKEN);
  if (update.message) await handleMessage(env, tg, update.message);
  if (update.callback_query) await handleCallback(env, tg, update.callback_query);
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    if (url.pathname === '/') return new Response('MegaufoBot is running. Use Telegram webhook.', { status: 200 });
    if (url.pathname === '/health') return Response.json({ ok: true });
    const expectedPath = `/webhook/${env.WEBHOOK_SECRET ?? 'telegram'}`;
    if (url.pathname !== expectedPath) return new Response('Not found', { status: 404 });
    if (request.method !== 'POST') return new Response('Method not allowed', { status: 405 });
    const update = await request.json<TelegramUpdate>();
    await handleUpdate(env, update);
    return Response.json({ ok: true });
  }
};

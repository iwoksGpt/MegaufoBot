import type { AiMovieDetails, Env, ImdbTitle, TelegramCallbackQuery, TelegramMessage, TelegramUpdate } from './types';
import { TelegramAPI } from './telegram';
import { t, type Lang } from './messages';
import { adminMenu, adminUserActions, mainMenu, popularMenu, profileKeyboard, ratingKeyboard, titleActions } from './keyboards';
import { displayTitle, getTitle, image, listCredits, listPopular, mediaType, ratingNumber, searchTitles, year } from './imdb';
import { enrichMovie, loadingDetails } from './ai';
import { resolveQueryAlias } from './aliases';
import {
  addFavorite, addUser, allActiveUserIds, clearAdminSession, getAdminSession, getSearchSession, getUserLang, getUserProfile,
  incrementStats, isBlocked, isFavorite, listFavorites, listUsers, logSearch, recentSearchLogs, removeFavorite, saveRating,
  saveSearchSession, setAdminSession, setBlocked, setUserLang, stats, type SearchSessionTitle
} from './db';

const PAGE_SIZE = 4;

function isAdmin(env: Env, userId?: number): boolean { return !!userId && (env.ADMIN_IDS ?? '').split(',').map((x) => x.trim()).includes(String(userId)); }
function escapeMd(v: unknown): string { return String(v ?? '').replace(/([_*`\[])/g, '\\$1'); }
function userLabel(row: Record<string, unknown>): string { return row.username ? `@${row.username}` : (`${row.first_name ?? ''} ${row.last_name ?? ''}`.trim() || String(row.user_id)); }
function toSessionTitle(t: ImdbTitle): SearchSessionTitle { return { id: t.id, title: displayTitle(t), year: year(t), type: mediaType(t), rating: ratingNumber(t) }; }

function searchResultsText(query: string, normalized: string | undefined, results: SearchSessionTitle[], page: number, lang: Lang): string {
  const total = results.length;
  const start = page * PAGE_SIZE;
  const items = results.slice(start, start + PAGE_SIZE);
  const lines = items.map((r, i) => `*${start + i + 1}.* ${r.type === 'movie' ? '🎬' : '📺'} ${escapeMd(r.title)} (${r.year}) — IMDb: ${escapeMd(r.rating)}`);
  return lang === 'en'
    ? `🫧 *Glass Search Results*\n\n🔎 Query: ${escapeMd(query)}${normalized && normalized !== query ? `\n🧭 Normalized: ${escapeMd(normalized)}` : ''}\n📌 Found: *${total}* result(s)\n📄 Page: *${page + 1}/${Math.max(1, Math.ceil(total / PAGE_SIZE))}*\n\n${lines.join('\n')}`
    : `🫧 *نتایج جستجوی شیشه‌ای*\n\n🔎 عبارت: ${escapeMd(query)}${normalized && normalized !== query ? `\n🧭 معادل جستجو: ${escapeMd(normalized)}` : ''}\n📌 تعداد نتایج یافت‌شده: *${total}*\n📄 صفحه: *${page + 1}/${Math.max(1, Math.ceil(total / PAGE_SIZE))}*\n\n${lines.join('\n')}`;
}

function searchResultsKeyboard(sessionId: string, results: SearchSessionTitle[], page: number, lang: Lang) {
  const totalPages = Math.max(1, Math.ceil(results.length / PAGE_SIZE));
  const start = page * PAGE_SIZE;
  const itemRows = results.slice(start, start + PAGE_SIZE).map((r, i) => ([{ text: `💎 ${start + i + 1} | ${r.type === 'movie' ? '🎬' : '📺'} ${r.title}`.slice(0, 58), callback_data: `d_${r.id}` }]));
  const nav = [] as { text: string; callback_data: string }[];
  if (page > 0) nav.push({ text: lang === 'en' ? '⬅️ Previous' : '⬅️ قبلی', callback_data: `sp_${sessionId}_${page - 1}` });
  if (page + 1 < totalPages) nav.push({ text: lang === 'en' ? 'Next ➡️' : 'بعدی ➡️', callback_data: `sp_${sessionId}_${page + 1}` });
  if (nav.length) itemRows.push(nav);
  itemRows.push([{ text: lang === 'en' ? '🏠 Home' : '🏠 خانه', callback_data: 'home' }]);
  return { inline_keyboard: itemRows };
}

function movieForm(details: AiMovieDetails, loading = false): string {
  const load = loading ? '⏳ ' : '';
  return `| 🎬 | - Movie Title: ${escapeMd(details.title)}\n\n` +
    `| ⭐ | - IMDb Rating: ${escapeMd(details.imdbRating)}\n\n` +
    `| 🍅 | - Rotten Tomatoes: ${load}${escapeMd(details.rottenTomatoes)}\n\n` +
    `| 🎭 | - Genre: ${escapeMd(details.genre)}\n\n` +
    `| ⏱️ | - Runtime: ${escapeMd(details.runtime)}\n\n` +
    `| 📆 | - Release Year: ${escapeMd(details.releaseYear)}\n\n` +
    `| 📌 | - خلاصه داستان:\n\n${load}${escapeMd(details.persianSummary)}`.slice(0, 1020);
}

async function reactToMessage(tg: TelegramAPI, m: TelegramMessage, emoji: string) { await tg.setMessageReaction(m.chat.id, m.message_id, emoji, true); }

async function bilingualSearch(query: string): Promise<{ normalized: string; results: ImdbTitle[] }> {
  const normalized = resolveQueryAlias(query);
  const [a, b] = await Promise.all([searchTitles(normalized, 16), normalized.toLowerCase() === query.trim().toLowerCase() ? [] : searchTitles(query, 8)]);
  const seen = new Set<string>();
  const results: ImdbTitle[] = [];
  for (const item of [...a, ...b]) if (item.id && !seen.has(item.id)) { seen.add(item.id); results.push(item); }
  return { normalized, results: results.slice(0, 20) };
}

async function handleSearch(env: Env, tg: TelegramAPI, message: TelegramMessage, query: string) {
  const lang = await getUserLang(env, message.from?.id);
  await incrementStats(env, 'searches');
  await reactToMessage(tg, message, '🔍');
  const { normalized, results } = await bilingualSearch(query);
  await logSearch(env, message.from?.id, query, normalized, lang, results.length);
  if (!results.length) return tg.sendMessage(message.chat.id, t(lang, 'noResults'), mainMenu(lang));
  const sessionResults = results.map(toSessionTitle);
  const sessionId = await saveSearchSession(env, message.from?.id, query, normalized, lang, sessionResults);
  return tg.sendMessage(message.chat.id, searchResultsText(query, normalized, sessionResults, 0, lang), searchResultsKeyboard(sessionId, sessionResults, 0, lang));
}

async function showTitle(env: Env, tg: TelegramAPI, chatId: number, userId: number, id: string, sourceMessageId?: number) {
  const lang = await getUserLang(env, userId);
  const title = await getTitle(id);
  if (!title) return tg.sendMessage(chatId, lang === 'en' ? '❌ Title not found.' : '❌ اطلاعات این عنوان پیدا نشد.', mainMenu(lang));
  await incrementStats(env, 'details');
  const fav = await isFavorite(env, userId, id);
  const markup = titleActions(id, mediaType(title), fav, lang);
  const loading = loadingDetails(title);
  const poster = image(title);
  let sent: any;
  if (poster) sent = await tg.sendPhoto(chatId, poster, movieForm(loading, true), markup).catch(() => tg.sendMessage(chatId, movieForm(loading, true), markup));
  else sent = await tg.sendMessage(chatId, movieForm(loading, true), markup);
  if (sourceMessageId) await tg.setMessageReaction(chatId, sourceMessageId, '🎬', true);
  const messageId = sent?.result?.message_id;
  try {
    const enriched = await enrichMovie(env, title);
    if (messageId && poster) await tg.editMessageCaption(chatId, messageId, movieForm(enriched.details), markup);
    else if (messageId) await tg.editMessageText(chatId, messageId, movieForm(enriched.details), markup);
  } catch {
    // keep loading/basic message if AI fails
  }
}

async function showProfile(env: Env, tg: TelegramAPI, chatId: number, userId: number) {
  const lang = await getUserLang(env, userId);
  const p = await getUserProfile(env, userId);
  if (!p) return tg.sendMessage(chatId, 'پروفایل پیدا نشد.', mainMenu(lang));
  const text = `👤 *پروفایل شما*\n\n🆔 آیدی: \`${p.user_id}\`\n👁 نام: ${escapeMd(userLabel(p as any))}\n🌐 زبان: *${p.language === 'en' ? 'English' : 'فارسی'}*\n📅 عضویت: ${p.join_date ?? '-'}\n🕒 آخرین فعالیت: ${p.last_seen ?? '-'}\n💬 پیام‌ها: ${p.message_count ?? 0}\n🔍 جستجوها: ${p.searches_count ?? 0}\n❤️ علاقه‌مندی‌ها: ${p.favorites_count ?? 0}\n⭐ امتیازها: ${p.ratings_count ?? 0}`;
  return tg.sendMessage(chatId, text, profileKeyboard(lang));
}

async function showFavorites(env: Env, tg: TelegramAPI, chatId: number, userId: number) {
  const lang = await getUserLang(env, userId);
  const rows = await listFavorites(env, userId);
  if (!rows.length) return tg.sendMessage(chatId, t(lang, 'favoritesEmpty'), mainMenu(lang));
  const buttons = rows.map((r: any) => [{ text: `${r.media_type === 'movie' ? '🎬' : '📺'} ${r.title}`, callback_data: `d_${r.title_id}` }]);
  buttons.push([{ text: '🏠 خانه', callback_data: 'home' }]);
  return tg.sendMessage(chatId, '❤️ *علاقه‌مندی‌های شما*', { inline_keyboard: buttons });
}

async function showAdminStats(env: Env, tg: TelegramAPI, chatId: number) {
  const s = await stats(env);
  return tg.sendMessage(chatId, `📊 *داشبورد مدیریت*\n\n👥 کل کاربران: ${s.totalUsers}\n⛔️ کاربران مسدود: ${s.blockedUsers}\n❤️ کل علاقه‌مندی‌ها: ${s.totalFavorites}\n⭐ کل امتیازها: ${s.totalRatings}\n\n*۷ روز اخیر*\n🔍 جستجوها: ${s.searches}\n📄 جزئیات: ${s.details}\n❤️ علاقه‌مندی جدید: ${s.favorites}\n🆕 کاربران جدید: ${s.new_users}`, adminMenu());
}

async function showAdminUsers(env: Env, tg: TelegramAPI, chatId: number, offset: number) {
  const { users, total, limit } = await listUsers(env, offset, 8);
  const rows = users.map((u) => [{ text: `${u.is_blocked ? '⛔️' : '👤'} ${userLabel(u as any)} — ${u.user_id}`, callback_data: `admin_user_${u.user_id}` }]);
  const nav = [] as any[];
  if (offset > 0) nav.push({ text: '⬅️ قبلی', callback_data: `admin_users_${Math.max(0, offset - limit)}` });
  if (offset + limit < total) nav.push({ text: 'بعدی ➡️', callback_data: `admin_users_${offset + limit}` });
  if (nav.length) rows.push(nav);
  rows.push([{ text: '👑 پنل مدیریت', callback_data: 'admin_home' }]);
  return tg.sendMessage(chatId, `👥 *کاربران*\nنمایش ${offset + 1} تا ${Math.min(offset + limit, total)} از ${total}`, { inline_keyboard: rows });
}

async function showAdminUser(env: Env, tg: TelegramAPI, chatId: number, userId: number) {
  const p = await getUserProfile(env, userId);
  if (!p) return tg.sendMessage(chatId, '❌ کاربر پیدا نشد.', adminMenu());
  const text = `👤 *جزئیات کاربر*\n🆔 ID: \`${p.user_id}\`\n👁 نام: ${escapeMd(userLabel(p as any))}\n🌐 زبان: ${p.language}\n⛔️ مسدود: ${p.is_blocked ? 'بله' : 'خیر'}\n📅 عضویت: ${p.join_date ?? '-'}\n🕒 آخرین فعالیت: ${p.last_seen ?? '-'}\n💬 پیام‌ها: ${p.message_count ?? 0}\n🔍 جستجوها: ${p.searches_count ?? 0}\n❤️ علاقه‌مندی‌ها: ${p.favorites_count ?? 0}`;
  return tg.sendMessage(chatId, text, adminUserActions(userId, Boolean(p.is_blocked)));
}

async function showAdminLogs(env: Env, tg: TelegramAPI, chatId: number) {
  const logs = await recentSearchLogs(env, 15);
  const text = logs.length ? logs.map((l: any, i) => `${i + 1}. \`${escapeMd(l.query)}\` → ${escapeMd(l.normalized_query)} | ${l.results_count} نتیجه | ${escapeMd(userLabel(l))}`).join('\n') : 'لاگی وجود ندارد.';
  return tg.sendMessage(chatId, `🔎 *آخرین جستجوها*\n\n${text}`, adminMenu());
}

async function handleBroadcastMessage(env: Env, tg: TelegramAPI, m: TelegramMessage, lang: Lang): Promise<boolean> {
  const uid = m.from?.id;
  if (!uid || !isAdmin(env, uid)) return false;
  const session = await getAdminSession(env, uid);
  if (session?.action !== 'broadcast') return false;
  const text = m.text?.trim() ?? '';
  if (['لغو', 'cancel', '/cancel'].includes(text.toLowerCase())) { await clearAdminSession(env, uid); await tg.sendMessage(m.chat.id, t(lang, 'broadcastCanceled'), adminMenu()); return true; }
  const ids = await allActiveUserIds(env, 1000);
  let sent = 0;
  for (const id of ids) if (id !== uid) try { await tg.sendMessage(id, `📢 *پیام مدیریت MegaufoBot*\n\n${escapeMd(text)}`); sent++; } catch {}
  await clearAdminSession(env, uid);
  await tg.sendMessage(m.chat.id, `${t(lang, 'broadcastDone')}\nارسال موفق: ${sent}`, adminMenu());
  return true;
}

async function handleMessage(env: Env, tg: TelegramAPI, m: TelegramMessage) {
  await addUser(env, m.from);
  const lang = await getUserLang(env, m.from?.id);
  if (await isBlocked(env, m.from?.id)) return tg.sendMessage(m.chat.id, t(lang, 'blocked'));
  if (await handleBroadcastMessage(env, tg, m, lang)) return;
  const text = (m.text ?? '').trim();
  if (!text) return;
  if (text === '/start') { await reactToMessage(tg, m, '👋'); return tg.sendMessage(m.chat.id, t(lang, 'welcome'), mainMenu(lang)); }
  if (text === '/help') { await reactToMessage(tg, m, '💡'); return tg.sendMessage(m.chat.id, t(lang, 'help'), mainMenu(lang)); }
  if (text === '/profile') { await reactToMessage(tg, m, '👤'); return showProfile(env, tg, m.chat.id, m.from?.id ?? 0); }
  if (text === '/popular') { await reactToMessage(tg, m, '🌟'); return tg.sendMessage(m.chat.id, t(lang, 'choosePopular'), popularMenu(lang)); }
  if (text === '/favorites') { await reactToMessage(tg, m, '❤️'); return showFavorites(env, tg, m.chat.id, m.from?.id ?? 0); }
  if (text === '/admin') { await reactToMessage(tg, m, '👑'); return isAdmin(env, m.from?.id) ? tg.sendMessage(m.chat.id, t(lang, 'adminTitle'), adminMenu()) : tg.sendMessage(m.chat.id, t(lang, 'adminDenied')); }
  return handleSearch(env, tg, m, text.replace(/^\/search\s*/i, ''));
}

async function handleCallback(env: Env, tg: TelegramAPI, c: TelegramCallbackQuery) {
  await addUser(env, c.from);
  const lang = await getUserLang(env, c.from.id);
  if (await isBlocked(env, c.from.id)) return;
  const data = c.data ?? '';
  const chatId = c.message?.chat.id;
  const messageId = c.message?.message_id;
  await tg.answerCallbackQuery(c.id).catch(() => undefined);
  if (!chatId) return;

  if (data === 'home') return tg.sendMessage(chatId, t(lang, 'welcome'), mainMenu(lang));
  if (data === 'help') return tg.sendMessage(chatId, t(lang, 'help'), mainMenu(lang));
  if (data === 'action_search') return tg.sendMessage(chatId, t(lang, 'searchPrompt'), mainMenu(lang));
  if (data === 'popular_menu') return tg.sendMessage(chatId, t(lang, 'choosePopular'), popularMenu(lang));
  if (data === 'favorites') return showFavorites(env, tg, chatId, c.from.id);
  if (data === 'profile') return showProfile(env, tg, chatId, c.from.id);
  if (data === 'lang_fa' || data === 'lang_en') { const newLang = data === 'lang_en' ? 'en' : 'fa'; await setUserLang(env, c.from.id, newLang); return tg.sendMessage(chatId, t(newLang, 'languageUpdated'), profileKeyboard(newLang)); }

  if (data.startsWith('sp_')) {
    const [, sid, pageRaw] = data.split('_');
    const session = await getSearchSession(env, sid);
    if (!session) return tg.sendMessage(chatId, '❌ این صفحه جستجو منقضی شده است.', mainMenu(lang));
    const page = Number(pageRaw || 0);
    return tg.editMessageText(chatId, messageId!, searchResultsText(session.query, session.normalized_query, session.results, page, session.language), searchResultsKeyboard(sid, session.results, page, session.language));
  }

  if (data.startsWith('d_')) return showTitle(env, tg, chatId, c.from.id, data.slice(2), messageId);
  if (data.startsWith('details_')) { const parts = data.split('_'); return showTitle(env, tg, chatId, c.from.id, parts[2], messageId); }

  if (data === 'popular_movie' || data === 'popular_tv') {
    const titles = await listPopular(data === 'popular_movie' ? 'MOVIE' : 'TV_SERIES');
    const results = titles.map(toSessionTitle);
    const sid = await saveSearchSession(env, c.from.id, data, data, lang, results);
    return tg.sendMessage(chatId, searchResultsText(data, data, results, 0, lang), searchResultsKeyboard(sid, results, 0, lang));
  }

  if (data.startsWith('fav_')) { const id = data.slice(4); const title = await getTitle(id); if (title) await addFavorite(env, c.from.id, title); if (messageId) await tg.setMessageReaction(chatId, messageId, '❤️', true); return showTitle(env, tg, chatId, c.from.id, id, messageId); }
  if (data.startsWith('unfav_')) { const id = data.slice(6); await removeFavorite(env, c.from.id, id); return showTitle(env, tg, chatId, c.from.id, id, messageId); }
  if (data.startsWith('rate_')) { const [, type, id] = data.split('_'); return tg.editMessageText(chatId, messageId!, '⭐ از ۱ تا ۱۰ چه امتیازی می‌دهی؟', ratingKeyboard(id, type, lang)); }
  if (data.startsWith('rated_')) { const [, type, id, score] = data.split('_'); await saveRating(env, c.from.id, id, type, Number(score)); if (messageId) await tg.setMessageReaction(chatId, messageId, '🔥', true); await tg.sendMessage(chatId, `✅ امتیاز ${score}/10 ثبت شد.`); return showTitle(env, tg, chatId, c.from.id, id, messageId); }
  if (data.startsWith('credits_')) { const names = await listCredits(data.slice(8)); return tg.sendMessage(chatId, names.length ? `🎭 *بازیگران / عوامل*\n\n${names.map(escapeMd).join('\n')}` : '❌ اطلاعات بازیگران در دسترس نیست.', mainMenu(lang)); }

  if (data === 'admin_home') return isAdmin(env, c.from.id) ? tg.sendMessage(chatId, t(lang, 'adminTitle'), adminMenu()) : tg.sendMessage(chatId, t(lang, 'adminDenied'));
  if (data === 'admin_stats') return isAdmin(env, c.from.id) ? showAdminStats(env, tg, chatId) : tg.sendMessage(chatId, t(lang, 'adminDenied'));
  if (data.startsWith('admin_users_')) return isAdmin(env, c.from.id) ? showAdminUsers(env, tg, chatId, Number(data.split('_')[2] ?? 0)) : tg.sendMessage(chatId, t(lang, 'adminDenied'));
  if (data.startsWith('admin_user_') && !data.startsWith('admin_user_favs_')) return isAdmin(env, c.from.id) ? showAdminUser(env, tg, chatId, Number(data.split('_')[2])) : tg.sendMessage(chatId, t(lang, 'adminDenied'));
  if (data.startsWith('admin_block_') || data.startsWith('admin_unblock_')) { if (!isAdmin(env, c.from.id)) return tg.sendMessage(chatId, t(lang, 'adminDenied')); const parts = data.split('_'); const block = parts[1] === 'block'; const target = Number(parts[2]); await setBlocked(env, target, block); return showAdminUser(env, tg, chatId, target); }
  if (data === 'admin_broadcast') { if (!isAdmin(env, c.from.id)) return tg.sendMessage(chatId, t(lang, 'adminDenied')); await setAdminSession(env, c.from.id, 'broadcast'); return tg.sendMessage(chatId, t(lang, 'broadcastPrompt'), adminMenu()); }
  if (data === 'admin_logs') return isAdmin(env, c.from.id) ? showAdminLogs(env, tg, chatId) : tg.sendMessage(chatId, t(lang, 'adminDenied'));
  if (data.startsWith('admin_user_favs_')) return isAdmin(env, c.from.id) ? showFavorites(env, tg, chatId, Number(data.split('_')[3])) : tg.sendMessage(chatId, t(lang, 'adminDenied'));

  return tg.sendMessage(chatId, '⚠️ این گزینه هنوز پشتیبانی نمی‌شود.', mainMenu(lang));
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
    await handleUpdate(env, await request.json<TelegramUpdate>());
    return Response.json({ ok: true });
  }
};

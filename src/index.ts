import type { Env, TelegramCallbackQuery, TelegramMessage, TelegramUpdate, ImdbTitle } from './types';
import { TelegramAPI } from './telegram';
import { t, type Lang } from './messages';
import { adminMenu, adminUserActions, mainMenu, popularMenu, profileKeyboard, ratingKeyboard, searchResultsKeyboard, titleActions } from './keyboards';
import { displayTitle, getTitle, image, listCredits, listPopular, mediaType, rating, searchTitles, year } from './imdb';
import { enrichMovie } from './ai';
import { createSearchSession, getSearchSession } from './searchSessions';
import { persianDisplayName, resolveQueryAlias } from './aliases';
import {
  addFavorite,
  addUser,
  allActiveUserIds,
  clearAdminSession,
  getAdminSession,
  getUserLang,
  getUserProfile,
  incrementStats,
  isBlocked,
  isFavorite,
  listFavorites,
  listUsers,
  logSearch,
  recentSearchLogs,
  removeFavorite,
  saveRating,
  setAdminSession,
  setBlocked,
  setUserLang,
  stats
} from './db';

function isAdmin(env: Env, userId?: number): boolean {
  if (!userId) return false;
  return (env.ADMIN_IDS ?? '').split(',').map((id) => id.trim()).includes(String(userId));
}

function escapeMd(value: unknown): string {
  return String(value ?? '').replace(/([_*`\[])/g, '\\$1');
}

function userLabel(row: Record<string, unknown>): string {
  const username = row.username ? `@${row.username}` : '';
  const name = `${row.first_name ?? ''} ${row.last_name ?? ''}`.trim();
  return username || name || String(row.user_id);
}


function runtime(title: ImdbTitle): string {
  return title.runtimeMinutes ? `${title.runtimeMinutes} minutes` : 'در حال دریافت...';
}

function imdbNumeric(title: ImdbTitle): string {
  return title.rating?.aggregateRating ? `${title.rating.aggregateRating}/10` : 'در حال دریافت...';
}

function genresText(title: ImdbTitle): string {
  return title.genres?.length ? title.genres.join(', ') : 'در حال دریافت...';
}

function movieSheetCaption(title: ImdbTitle, opts?: { rotten?: string; summary?: string; loading?: boolean }): string {
  const loading = opts?.loading ?? false;
  const load = loading ? '⏳' : '';
  const summary = opts?.summary ?? '⏳ در حال نوشتن خلاصه اختصاصی فارسی...';
  const rotten = opts?.rotten ?? '⏳';
  return `| 🎬 | - Movie Title: ${escapeMd(displayTitle(title))}

` +
    `| ⭐ | - IMDb Rating: ${escapeMd(imdbNumeric(title))}

` +
    `| 🍅 | - Rotten Tomatoes: ${escapeMd(rotten)} ${load}

` +
    `| 🎭 | - Genre: ${escapeMd(genresText(title))}

` +
    `| ⏱️ | - Runtime: ${escapeMd(runtime(title))}

` +
    `| 📆 | - Release Year: ${escapeMd(year(title))}

` +
    `| 📌 | - خلاصه داستان:

${escapeMd(summary).slice(0, 620)}`;
}

function searchListText(query: string, normalized: string, results: ImdbTitle[], page: number, perPage = 4): string {
  const total = results.length;
  const start = page * perPage;
  const pageItems = results.slice(start, start + perPage);
  const lines = pageItems.map((title, localIndex) => {
    const n = start + localIndex + 1;
    return `${n}. ${displayTitle(title)} (${year(title)}) — IMDb ${imdbNumeric(title)}`;
  });
  return `🫧 *نتایج جستجوی شیشه‌ای*

` +
    `🔎 عبارت: ${escapeMd(query)}${normalized !== query ? `
🧠 معادل جستجو: ${escapeMd(normalized)}` : ''}
` +
    `🎞 تعداد نتایج یافت شده: *${total}*
` +
    `📄 صفحه: *${page + 1}/${Math.max(1, Math.ceil(total / perPage))}*

` +
    lines.map(escapeMd).join('\n') +
    `

برای باز کردن هر فیلم، روی کلید شماره‌دار شیشه‌ای پایین پیام بزن.`;
}

function compactSearchCaption(title: ImdbTitle, index: number, query: string, lang: Lang): string {
  const english = displayTitle(title);
  const fa = persianDisplayName(english);
  const display = lang === 'en' ? english : (fa ?? english);
  const typeIcon = mediaType(title) === 'movie' ? '🎬' : '📺';
  const genres = title.genres?.slice(0, 4).join('، ') || (lang === 'en' ? 'Unknown' : 'نامشخص');
  return `✨ *${lang === 'en' ? 'Result' : 'نتیجه'} ${index}* — ${typeIcon}\n` +
    `*${escapeMd(display)}*${fa ? `\n_${escapeMd(english)}_` : ''}\n\n` +
    `🫧 ${lang === 'en' ? 'Search' : 'جستجو'}: ${escapeMd(query)}\n` +
    `🗓 ${year(title)}   ⭐ ${escapeMd(rating(title))}\n` +
    `🎭 ${escapeMd(genres)}`;
}

async function reactToMessage(tg: TelegramAPI, message: TelegramMessage, emoji: string) {
  await tg.setMessageReaction(message.chat.id, message.message_id, emoji, true);
}

async function progressiveEditMovieCaption(tg: TelegramAPI, chatId: number, messageId: number, title: ImdbTitle, markup: ReturnType<typeof titleActions>, finalSummary: string, rotten: string) {
  const chunks = [
    finalSummary.slice(0, Math.max(80, Math.ceil(finalSummary.length * 0.35))),
    finalSummary.slice(0, Math.max(160, Math.ceil(finalSummary.length * 0.7))),
    finalSummary
  ];
  for (let i = 0; i < chunks.length; i++) {
    await new Promise((resolve) => setTimeout(resolve, i === 0 ? 350 : 550));
    await tg.editMessageCaption(chatId, messageId, movieSheetCaption(title, { rotten: i === 0 ? '⏳' : rotten, summary: chunks[i], loading: i < chunks.length - 1 }), markup).catch(() => undefined);
  }
}

async function showTitle(env: Env, tg: TelegramAPI, chatId: number, userId: number, id: string) {
  const lang = await getUserLang(env, userId);
  const title = await getTitle(id);
  if (!title) return tg.sendMessage(chatId, lang === 'en' ? '❌ Title not found.' : '❌ اطلاعات این عنوان پیدا نشد.', mainMenu(lang));
  await incrementStats(env, 'details');
  const fav = await isFavorite(env, userId, id);
  const markup = titleActions(id, mediaType(title), fav, lang);
  const initialCaption = movieSheetCaption(title, { loading: true });
  const poster = image(title);
  let sentMessageId: number | undefined;
  if (poster) {
    const sent = await tg.sendPhoto(chatId, poster, initialCaption, markup).catch(() => undefined) as { result?: { message_id?: number } } | undefined;
    sentMessageId = sent?.result?.message_id;
    if (!sentMessageId) {
      const msg = await tg.sendMessage(chatId, initialCaption, markup) as { result?: { message_id?: number } };
      sentMessageId = msg.result?.message_id;
    }
  } else {
    const msg = await tg.sendMessage(chatId, initialCaption, markup) as { result?: { message_id?: number } };
    sentMessageId = msg.result?.message_id;
  }
  const enriched = await enrichMovie(env, title);
  if (sentMessageId) {
    if (poster) await progressiveEditMovieCaption(tg, chatId, sentMessageId, title, markup, enriched.summaryFa, enriched.rottenTomatoes ?? 'نامشخص');
    else await tg.editMessageText(chatId, sentMessageId, movieSheetCaption(title, { rotten: enriched.rottenTomatoes ?? 'نامشخص', summary: enriched.summaryFa }), markup).catch(() => undefined);
  }
}

async function bilingualSearch(query: string): Promise<{ normalized: string; results: ImdbTitle[] }> {
  const normalized = resolveQueryAlias(query);
  const batches = await Promise.all([
    searchTitles(normalized, 20),
    normalized.toLowerCase() === query.trim().toLowerCase() ? Promise.resolve([]) : searchTitles(query, 8)
  ]);
  const seen = new Set<string>();
  const results: ImdbTitle[] = [];
  for (const title of batches.flat()) {
    if (!title.id || seen.has(title.id)) continue;
    seen.add(title.id);
    results.push(title);
  }
  return { normalized, results: results.slice(0, 20) };
}

async function handleSearch(env: Env, tg: TelegramAPI, message: TelegramMessage, query: string) {
  const lang = await getUserLang(env, message.from?.id);
  await incrementStats(env, 'searches');
  await reactToMessage(tg, message, '🔍');
  const { normalized, results } = await bilingualSearch(query);
  await logSearch(env, message.from?.id, query, normalized, lang, results.length);
  if (!results.length) return tg.sendMessage(message.chat.id, t(lang, 'noResults'), mainMenu(lang));
  const sessionId = await createSearchSession(env, message.from?.id, query, normalized, results);
  return tg.sendMessage(message.chat.id, searchListText(query, normalized, results, 0), searchResultsKeyboard(sessionId, 0, results.length));
}

async function showProfile(env: Env, tg: TelegramAPI, chatId: number, userId: number) {
  const lang = await getUserLang(env, userId);
  const profile = await getUserProfile(env, userId);
  if (!profile) return tg.sendMessage(chatId, lang === 'en' ? 'Profile not found.' : 'پروفایل پیدا نشد.', mainMenu(lang));
  const name = userLabel(profile as unknown as Record<string, unknown>);
  const text = lang === 'en'
    ? `👤 *Your Profile*\n\n🆔 ID: \`${profile.user_id}\`\n👁 Name: ${escapeMd(name)}\n🌐 Language: *${profile.language === 'en' ? 'English' : 'Persian'}*\n📅 Joined: ${profile.join_date ?? '-'}\n🕒 Last seen: ${profile.last_seen ?? '-'}\n💬 Messages: ${profile.message_count ?? 0}\n🔍 Searches: ${profile.searches_count ?? 0}\n❤️ Favorites: ${profile.favorites_count ?? 0}\n⭐ Ratings: ${profile.ratings_count ?? 0}`
    : `👤 *پروفایل شما*\n\n🆔 آیدی: \`${profile.user_id}\`\n👁 نام: ${escapeMd(name)}\n🌐 زبان: *${profile.language === 'en' ? 'انگلیسی' : 'فارسی'}*\n📅 عضویت: ${profile.join_date ?? '-'}\n🕒 آخرین فعالیت: ${profile.last_seen ?? '-'}\n💬 پیام‌ها: ${profile.message_count ?? 0}\n🔍 جستجوها: ${profile.searches_count ?? 0}\n❤️ علاقه‌مندی‌ها: ${profile.favorites_count ?? 0}\n⭐ امتیازها: ${profile.ratings_count ?? 0}`;
  return tg.sendMessage(chatId, text, profileKeyboard(lang));
}

async function showFavorites(env: Env, tg: TelegramAPI, chatId: number, userId: number) {
  const lang = await getUserLang(env, userId);
  const rows = await listFavorites(env, userId);
  if (!rows.length) return tg.sendMessage(chatId, t(lang, 'favoritesEmpty'), mainMenu(lang));
  const buttons = rows.map((row: Record<string, unknown>) => [{
    text: `${row.media_type === 'movie' ? '🎬' : '📺'} ${row.title}`,
    callback_data: `details_${row.media_type}_${row.title_id}`
  }]);
  buttons.push([{ text: lang === 'en' ? '🔙 Back' : '🔙 بازگشت', callback_data: 'home' }]);
  return tg.sendMessage(chatId, lang === 'en' ? '❤️ *Your Favorites*' : '❤️ *علاقه‌مندی‌های شما*', { inline_keyboard: buttons });
}

async function showAdminUsers(env: Env, tg: TelegramAPI, chatId: number, offset: number) {
  const { users, total, limit } = await listUsers(env, offset, 8);
  const rows = users.map((u) => [{ text: `${u.is_blocked ? '⛔️' : '👤'} ${userLabel(u as unknown as Record<string, unknown>)} — ${u.user_id}`, callback_data: `admin_user_${u.user_id}` }]);
  const nav = [];
  if (offset > 0) nav.push({ text: '⬅️ قبلی', callback_data: `admin_users_${Math.max(0, offset - limit)}` });
  if (offset + limit < total) nav.push({ text: 'بعدی ➡️', callback_data: `admin_users_${offset + limit}` });
  if (nav.length) rows.push(nav);
  rows.push([{ text: '👑 پنل مدیریت', callback_data: 'admin_home' }]);
  await tg.sendMessage(chatId, `👥 *کاربران*\n\nنمایش ${offset + 1} تا ${Math.min(offset + limit, total)} از ${total}`, { inline_keyboard: rows });
}

async function showAdminUser(env: Env, tg: TelegramAPI, chatId: number, userId: number) {
  const profile = await getUserProfile(env, userId);
  if (!profile) return tg.sendMessage(chatId, '❌ کاربر پیدا نشد.', adminMenu());
  const text = `👤 *جزئیات کاربر*\n\n🆔 ID: \`${profile.user_id}\`\n👁 نام: ${escapeMd(userLabel(profile as unknown as Record<string, unknown>))}\n🌐 زبان: ${profile.language}\n⛔️ مسدود: ${profile.is_blocked ? 'بله' : 'خیر'}\n📅 عضویت: ${profile.join_date ?? '-'}\n🕒 آخرین فعالیت: ${profile.last_seen ?? '-'}\n💬 پیام‌ها: ${profile.message_count ?? 0}\n🔍 جستجوها: ${profile.searches_count ?? 0}\n❤️ علاقه‌مندی‌ها: ${profile.favorites_count ?? 0}\n⭐ امتیازها: ${profile.ratings_count ?? 0}`;
  return tg.sendMessage(chatId, text, adminUserActions(userId, Boolean(profile.is_blocked)));
}

async function showAdminStats(env: Env, tg: TelegramAPI, chatId: number) {
  const s = await stats(env);
  const text = `📊 *داشبورد مدیریت*\n\n👥 کل کاربران: ${s.totalUsers}\n⛔️ کاربران مسدود: ${s.blockedUsers}\n❤️ کل علاقه‌مندی‌ها: ${s.totalFavorites}\n⭐ کل امتیازها: ${s.totalRatings}\n\n*۷ روز اخیر*\n🔍 جستجوها: ${s.searches}\n📄 جزئیات بازشده: ${s.details}\n❤️ علاقه‌مندی‌های جدید: ${s.favorites}\n🆕 کاربران جدید: ${s.new_users}`;
  return tg.sendMessage(chatId, text, adminMenu());
}

async function showAdminLogs(env: Env, tg: TelegramAPI, chatId: number) {
  const logs = await recentSearchLogs(env, 15);
  if (!logs.length) return tg.sendMessage(chatId, '🔎 هنوز لاگی ثبت نشده.', adminMenu());
  const text = logs.map((log, i) => `${i + 1}. \`${escapeMd(log.query)}\` → ${escapeMd(log.normalized_query)} | ${log.results_count} نتیجه | ${escapeMd(userLabel(log))}`).join('\n');
  return tg.sendMessage(chatId, `🔎 *آخرین جستجوها*\n\n${text}`, adminMenu());
}

async function handleBroadcastMessage(env: Env, tg: TelegramAPI, message: TelegramMessage, lang: Lang): Promise<boolean> {
  const userId = message.from?.id;
  if (!userId || !isAdmin(env, userId)) return false;
  const session = await getAdminSession(env, userId);
  if (session?.action !== 'broadcast') return false;
  const text = message.text?.trim() ?? '';
  if (!text) return true;
  if (['لغو', 'cancel', '/cancel'].includes(text.toLowerCase())) {
    await clearAdminSession(env, userId);
    await tg.sendMessage(message.chat.id, t(lang, 'broadcastCanceled'), adminMenu());
    return true;
  }
  const ids = await allActiveUserIds(env, 1000);
  let sent = 0;
  for (const id of ids) {
    if (id === userId) continue;
    try {
      await tg.sendMessage(id, `📢 *پیام مدیریت MegaufoBot*\n\n${escapeMd(text)}`);
      sent++;
    } catch {
      // Ignore blocked/deleted chats.
    }
  }
  await clearAdminSession(env, userId);
  await tg.sendMessage(message.chat.id, `${t(lang, 'broadcastDone')}\nارسال موفق: ${sent}`, adminMenu());
  return true;
}

async function handleMessage(env: Env, tg: TelegramAPI, message: TelegramMessage) {
  await addUser(env, message.from);
  const lang = await getUserLang(env, message.from?.id);
  if (await isBlocked(env, message.from?.id)) return tg.sendMessage(message.chat.id, t(lang, 'blocked'));
  if (await handleBroadcastMessage(env, tg, message, lang)) return;
  const text = (message.text ?? '').trim();
  if (!text) return;

  if (text === '/start') { await reactToMessage(tg, message, '👋'); return tg.sendMessage(message.chat.id, t(lang, 'welcome'), mainMenu(lang)); }
  if (text === '/help') { await reactToMessage(tg, message, '💡'); return tg.sendMessage(message.chat.id, t(lang, 'help'), mainMenu(lang)); }
  if (text === '/profile') { await reactToMessage(tg, message, '👤'); return showProfile(env, tg, message.chat.id, message.from?.id ?? 0); }
  if (text === '/popular') { await reactToMessage(tg, message, '🌟'); return tg.sendMessage(message.chat.id, t(lang, 'choosePopular'), popularMenu(lang)); }
  if (text === '/favorites') { await reactToMessage(tg, message, '❤️'); return showFavorites(env, tg, message.chat.id, message.from?.id ?? 0); }
  if (text === '/admin') {
    await reactToMessage(tg, message, '👑');
    if (!isAdmin(env, message.from?.id)) return tg.sendMessage(message.chat.id, t(lang, 'adminDenied'));
    return tg.sendMessage(message.chat.id, t(lang, 'adminTitle'), adminMenu());
  }
  await handleSearch(env, tg, message, text.replace(/^\/search\s*/i, ''));
}

async function handleCallback(env: Env, tg: TelegramAPI, callback: TelegramCallbackQuery) {
  await addUser(env, callback.from);
  const lang = await getUserLang(env, callback.from.id);
  if (await isBlocked(env, callback.from.id)) return;
  const data = callback.data ?? '';
  const chatId = callback.message?.chat.id;
  const messageId = callback.message?.message_id;
  await tg.answerCallbackQuery(callback.id).catch(() => undefined);
  if (!chatId) return;

  if (data === 'home') return tg.sendMessage(chatId, t(lang, 'welcome'), mainMenu(lang));
  if (data === 'help') return tg.sendMessage(chatId, t(lang, 'help'), mainMenu(lang));
  if (data === 'action_search') return tg.sendMessage(chatId, t(lang, 'searchPrompt'), mainMenu(lang));
  if (data === 'popular_menu') return tg.sendMessage(chatId, t(lang, 'choosePopular'), popularMenu(lang));
  if (data === 'favorites') return showFavorites(env, tg, chatId, callback.from.id);
  if (data === 'profile') return showProfile(env, tg, chatId, callback.from.id);
  if (data === 'lang_fa' || data === 'lang_en') {
    const newLang: Lang = data === 'lang_en' ? 'en' : 'fa';
    await setUserLang(env, callback.from.id, newLang);
    return tg.sendMessage(chatId, t(newLang, 'languageUpdated'), profileKeyboard(newLang));
  }

  if (data === 'admin_home') {
    if (!isAdmin(env, callback.from.id)) return tg.sendMessage(chatId, t(lang, 'adminDenied'));
    return tg.sendMessage(chatId, t(lang, 'adminTitle'), adminMenu());
  }
  if (data === 'admin_stats') {
    if (!isAdmin(env, callback.from.id)) return tg.sendMessage(chatId, t(lang, 'adminDenied'));
    return showAdminStats(env, tg, chatId);
  }
  if (data.startsWith('admin_users_')) {
    if (!isAdmin(env, callback.from.id)) return tg.sendMessage(chatId, t(lang, 'adminDenied'));
    return showAdminUsers(env, tg, chatId, Number(data.split('_')[2] ?? 0));
  }
  if (data.startsWith('admin_user_') && !data.startsWith('admin_user_favs_')) {
    if (!isAdmin(env, callback.from.id)) return tg.sendMessage(chatId, t(lang, 'adminDenied'));
    return showAdminUser(env, tg, chatId, Number(data.split('_')[2]));
  }
  if (data.startsWith('admin_block_') || data.startsWith('admin_unblock_')) {
    if (!isAdmin(env, callback.from.id)) return tg.sendMessage(chatId, t(lang, 'adminDenied'));
    const parts = data.split('_');
    const block = parts[1] === 'block';
    const targetId = Number(parts[2]);
    await setBlocked(env, targetId, block);
    return showAdminUser(env, tg, chatId, targetId);
  }
  if (data === 'admin_broadcast') {
    if (!isAdmin(env, callback.from.id)) return tg.sendMessage(chatId, t(lang, 'adminDenied'));
    await setAdminSession(env, callback.from.id, 'broadcast');
    return tg.sendMessage(chatId, t(lang, 'broadcastPrompt'), adminMenu());
  }
  if (data === 'admin_logs') {
    if (!isAdmin(env, callback.from.id)) return tg.sendMessage(chatId, t(lang, 'adminDenied'));
    return showAdminLogs(env, tg, chatId);
  }
  if (data.startsWith('admin_user_favs_')) {
    if (!isAdmin(env, callback.from.id)) return tg.sendMessage(chatId, t(lang, 'adminDenied'));
    const targetId = Number(data.split('_')[3]);
    return showFavorites(env, tg, chatId, targetId);
  }

  if (data === 'popular_movie' || data === 'popular_tv') {
    const titles = await listPopular(data === 'popular_movie' ? 'MOVIE' : 'TV_SERIES');
    const query = data === 'popular_movie' ? 'فیلم‌های محبوب' : 'سریال‌های محبوب';
    const sessionId = await createSearchSession(env, callback.from.id, query, query, titles);
    return tg.sendMessage(chatId, searchListText(query, query, titles, 0), searchResultsKeyboard(sessionId, 0, titles.length));
  }

  if (data.startsWith('s_')) {
    const [, sessionId, pageRaw] = data.split('_');
    const session = await getSearchSession(env, sessionId);
    if (!session) return tg.sendMessage(chatId, '❌ نتایج قبلی منقضی شده‌اند. دوباره جستجو کن.', mainMenu(lang));
    const page = Math.max(0, Number(pageRaw) || 0);
    return tg.editMessageText(chatId, messageId!, searchListText(session.query, session.normalizedQuery, session.results, page), searchResultsKeyboard(session.id, page, session.total));
  }

  if (data.startsWith('r_')) {
    const [, sessionId, indexRaw] = data.split('_');
    const session = await getSearchSession(env, sessionId);
    if (!session) return tg.sendMessage(chatId, '❌ نتایج قبلی منقضی شده‌اند. دوباره جستجو کن.', mainMenu(lang));
    const title = session.results[Number(indexRaw)];
    if (!title?.id) return tg.sendMessage(chatId, '❌ این نتیجه در دسترس نیست.', mainMenu(lang));
    if (messageId) await tg.setMessageReaction(chatId, messageId, '🎬', true);
    return showTitle(env, tg, chatId, callback.from.id, title.id);
  }

  if (data.startsWith('details_')) {
    const [, , id] = data.split('_');
    return showTitle(env, tg, chatId, callback.from.id, id);
  }
  if (data.startsWith('fav_')) {
    const id = data.slice(4);
    const title = await getTitle(id);
    if (!title) return tg.sendMessage(chatId, '❌ Title not found.');
    await addFavorite(env, callback.from.id, title);
    await tg.setMessageReaction(chatId, messageId ?? 0, '❤️', true);
    return showTitle(env, tg, chatId, callback.from.id, id);
  }
  if (data.startsWith('unfav_')) {
    const id = data.slice(6);
    await removeFavorite(env, callback.from.id, id);
    return showTitle(env, tg, chatId, callback.from.id, id);
  }
  if (data.startsWith('rate_')) {
    const [, type, id] = data.split('_');
    return tg.editMessageText(chatId, messageId!, lang === 'en' ? '⭐ Rate from 1 to 10:' : '⭐ از ۱ تا ۱۰ چه امتیازی می‌دهی؟', ratingKeyboard(id, type, lang));
  }
  if (data.startsWith('rated_')) {
    const [, type, id, score] = data.split('_');
    await saveRating(env, callback.from.id, id, type, Number(score));
    await tg.setMessageReaction(chatId, messageId ?? 0, '🔥', true);
    await tg.sendMessage(chatId, lang === 'en' ? `✅ Your ${score}/10 rating was saved.` : `✅ امتیاز ${score}/10 ثبت شد.`);
    return showTitle(env, tg, chatId, callback.from.id, id);
  }
  if (data.startsWith('credits_')) {
    const id = data.slice(8);
    const names = await listCredits(id);
    return tg.sendMessage(chatId, names.length ? `🎭 *${lang === 'en' ? 'Cast / Crew' : 'بازیگران / عوامل'}*\n\n${names.map(escapeMd).join('\n')}` : (lang === 'en' ? '❌ Credits are unavailable.' : '❌ اطلاعات بازیگران در دسترس نیست.'), mainMenu(lang));
  }
  return tg.sendMessage(chatId, lang === 'en' ? '⚠️ Unsupported option.' : '⚠️ این گزینه هنوز پشتیبانی نمی‌شود.', mainMenu(lang));
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

import type { Env, TelegramUser } from './types';
import type { ImdbTitle } from './types';
import { displayTitle, image, mediaType } from './imdb';
import type { Lang } from './messages';

export type UserProfile = {
  user_id: number;
  username?: string | null;
  first_name?: string | null;
  last_name?: string | null;
  language?: string | null;
  join_date?: string | null;
  last_seen?: string | null;
  message_count?: number | null;
  is_blocked?: number | null;
  favorites_count?: number;
  ratings_count?: number;
  searches_count?: number;
};

export async function addUser(env: Env, user?: TelegramUser) {
  if (!user) return;
  const exists = await env.DB.prepare('SELECT 1 FROM users WHERE user_id = ?').bind(user.id).first();
  await env.DB.prepare(
    'INSERT OR IGNORE INTO users (user_id, username, first_name, last_name, language, last_seen, message_count) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 0)'
  ).bind(user.id, user.username ?? null, user.first_name ?? null, user.last_name ?? null, user.language_code?.startsWith('en') ? 'en' : 'fa').run();
  await env.DB.prepare(
    'UPDATE users SET username = ?, first_name = ?, last_name = ?, last_seen = CURRENT_TIMESTAMP, message_count = COALESCE(message_count, 0) + 1 WHERE user_id = ?'
  ).bind(user.username ?? null, user.first_name ?? null, user.last_name ?? null, user.id).run();
  if (!exists) await incrementStats(env, 'new_users');
}

export async function getUserLang(env: Env, userId?: number): Promise<Lang> {
  if (!userId) return 'fa';
  const row = await env.DB.prepare('SELECT language FROM users WHERE user_id = ?').bind(userId).first<{ language?: string }>();
  return row?.language === 'en' ? 'en' : 'fa';
}

export async function setUserLang(env: Env, userId: number, lang: Lang) {
  await env.DB.prepare('UPDATE users SET language = ? WHERE user_id = ?').bind(lang, userId).run();
}

export async function isBlocked(env: Env, userId?: number): Promise<boolean> {
  if (!userId) return false;
  const row = await env.DB.prepare('SELECT is_blocked FROM users WHERE user_id = ?').bind(userId).first<{ is_blocked?: number }>();
  return Boolean(row?.is_blocked);
}

export async function setBlocked(env: Env, userId: number, blocked: boolean) {
  await env.DB.prepare('UPDATE users SET is_blocked = ? WHERE user_id = ?').bind(blocked ? 1 : 0, userId).run();
}

export async function getUserProfile(env: Env, userId: number): Promise<UserProfile | null> {
  const row = await env.DB.prepare('SELECT * FROM users WHERE user_id = ?').bind(userId).first<UserProfile>();
  if (!row) return null;
  const fav = await env.DB.prepare('SELECT COUNT(*) AS count FROM favorites WHERE user_id = ?').bind(userId).first<{ count: number }>();
  const rat = await env.DB.prepare('SELECT COUNT(*) AS count FROM ratings WHERE user_id = ?').bind(userId).first<{ count: number }>();
  const sea = await env.DB.prepare('SELECT COUNT(*) AS count FROM search_logs WHERE user_id = ?').bind(userId).first<{ count: number }>();
  return { ...row, favorites_count: fav?.count ?? 0, ratings_count: rat?.count ?? 0, searches_count: sea?.count ?? 0 };
}

export async function listUsers(env: Env, offset = 0, limit = 8) {
  const { results } = await env.DB.prepare(
    'SELECT user_id, username, first_name, last_name, language, join_date, last_seen, message_count, is_blocked FROM users ORDER BY COALESCE(last_seen, join_date) DESC LIMIT ? OFFSET ?'
  ).bind(limit, offset).all<UserProfile>();
  const total = await env.DB.prepare('SELECT COUNT(*) AS count FROM users').first<{ count: number }>();
  return { users: results, total: total?.count ?? 0, offset, limit };
}

export async function incrementStats(env: Env, column: 'searches' | 'details' | 'favorites' | 'new_users') {
  const today = new Date().toISOString().slice(0, 10);
  await env.DB.prepare('INSERT OR IGNORE INTO statistics (date) VALUES (?)').bind(today).run();
  await env.DB.prepare(`UPDATE statistics SET ${column} = ${column} + 1 WHERE date = ?`).bind(today).run();
}

export async function logSearch(env: Env, userId: number | undefined, query: string, normalizedQuery: string, language: Lang, resultsCount: number) {
  await env.DB.prepare('INSERT INTO search_logs (user_id, query, normalized_query, language, results_count) VALUES (?, ?, ?, ?, ?)')
    .bind(userId ?? null, query, normalizedQuery, language, resultsCount).run();
}

export async function recentSearchLogs(env: Env, limit = 12) {
  const { results } = await env.DB.prepare(
    'SELECT s.user_id, s.query, s.normalized_query, s.language, s.results_count, s.created_at, u.username, u.first_name FROM search_logs s LEFT JOIN users u ON u.user_id = s.user_id ORDER BY s.created_at DESC LIMIT ?'
  ).bind(limit).all<Record<string, unknown>>();
  return results;
}

export async function addFavorite(env: Env, userId: number, title: ImdbTitle) {
  await env.DB.prepare(
    'INSERT OR IGNORE INTO favorites (user_id, title_id, media_type, title, image_url) VALUES (?, ?, ?, ?, ?)'
  ).bind(userId, title.id, mediaType(title), displayTitle(title), image(title) ?? null).run();
  await incrementStats(env, 'favorites');
}

export async function removeFavorite(env: Env, userId: number, titleId: string) {
  await env.DB.prepare('DELETE FROM favorites WHERE user_id = ? AND title_id = ?').bind(userId, titleId).run();
}

export async function isFavorite(env: Env, userId: number, titleId: string): Promise<boolean> {
  const row = await env.DB.prepare('SELECT 1 FROM favorites WHERE user_id = ? AND title_id = ? LIMIT 1').bind(userId, titleId).first();
  return Boolean(row);
}

export async function listFavorites(env: Env, userId: number, limit = 20) {
  const { results } = await env.DB.prepare(
    'SELECT title_id, media_type, title, image_url, added_date FROM favorites WHERE user_id = ? ORDER BY added_date DESC LIMIT ?'
  ).bind(userId, limit).all();
  return results;
}

export async function saveRating(env: Env, userId: number, titleId: string, type: string, rating: number) {
  await env.DB.prepare(
    'INSERT OR REPLACE INTO ratings (user_id, title_id, media_type, rating) VALUES (?, ?, ?, ?)'
  ).bind(userId, titleId, type, rating).run();
}

export async function stats(env: Env) {
  const totalUsers = await env.DB.prepare('SELECT COUNT(*) AS count FROM users').first<{ count: number }>();
  const blocked = await env.DB.prepare('SELECT COUNT(*) AS count FROM users WHERE is_blocked = 1').first<{ count: number }>();
  const favs = await env.DB.prepare('SELECT COUNT(*) AS count FROM favorites').first<{ count: number }>();
  const ratings = await env.DB.prepare('SELECT COUNT(*) AS count FROM ratings').first<{ count: number }>();
  const last7 = await env.DB.prepare(
    "SELECT COALESCE(SUM(searches),0) AS searches, COALESCE(SUM(details),0) AS details, COALESCE(SUM(favorites),0) AS favorites, COALESCE(SUM(new_users),0) AS new_users FROM statistics WHERE date >= date('now','-7 days')"
  ).first<{ searches: number; details: number; favorites: number; new_users: number }>();
  return { totalUsers: totalUsers?.count ?? 0, blockedUsers: blocked?.count ?? 0, totalFavorites: favs?.count ?? 0, totalRatings: ratings?.count ?? 0, ...(last7 ?? { searches: 0, details: 0, favorites: 0, new_users: 0 }) };
}

export async function setAdminSession(env: Env, adminId: number, action: string, payload?: string) {
  await env.DB.prepare('INSERT OR REPLACE INTO admin_sessions (admin_id, action, payload) VALUES (?, ?, ?)').bind(adminId, action, payload ?? null).run();
}

export async function getAdminSession(env: Env, adminId: number) {
  return env.DB.prepare('SELECT action, payload FROM admin_sessions WHERE admin_id = ?').bind(adminId).first<{ action: string; payload?: string }>();
}

export async function clearAdminSession(env: Env, adminId: number) {
  await env.DB.prepare('DELETE FROM admin_sessions WHERE admin_id = ?').bind(adminId).run();
}

export async function allActiveUserIds(env: Env, limit = 1000): Promise<number[]> {
  const { results } = await env.DB.prepare('SELECT user_id FROM users WHERE COALESCE(is_blocked,0) = 0 ORDER BY last_seen DESC LIMIT ?').bind(limit).all<{ user_id: number }>();
  return results.map((row) => row.user_id);
}

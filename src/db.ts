import type { Env, TelegramUser } from './types';
import type { ImdbTitle } from './types';
import { displayTitle, image, mediaType } from './imdb';

export async function addUser(env: Env, user?: TelegramUser) {
  if (!user) return;
  const exists = await env.DB.prepare('SELECT 1 FROM users WHERE user_id = ?').bind(user.id).first();
  await env.DB.prepare(
    'INSERT OR IGNORE INTO users (user_id, username, first_name, last_name, language) VALUES (?, ?, ?, ?, ?)'
  ).bind(user.id, user.username ?? null, user.first_name ?? null, user.last_name ?? null, user.language_code ?? 'fa').run();
  if (!exists) await incrementStats(env, 'new_users');
}

export async function incrementStats(env: Env, column: 'searches' | 'details' | 'favorites' | 'new_users') {
  const today = new Date().toISOString().slice(0, 10);
  await env.DB.prepare('INSERT OR IGNORE INTO statistics (date) VALUES (?)').bind(today).run();
  await env.DB.prepare(`UPDATE statistics SET ${column} = ${column} + 1 WHERE date = ?`).bind(today).run();
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

export async function listFavorites(env: Env, userId: number) {
  const { results } = await env.DB.prepare(
    'SELECT title_id, media_type, title, image_url, added_date FROM favorites WHERE user_id = ? ORDER BY added_date DESC LIMIT 20'
  ).bind(userId).all();
  return results;
}

export async function saveRating(env: Env, userId: number, titleId: string, type: string, rating: number) {
  await env.DB.prepare(
    'INSERT OR REPLACE INTO ratings (user_id, title_id, media_type, rating) VALUES (?, ?, ?, ?)'
  ).bind(userId, titleId, type, rating).run();
}

export async function stats(env: Env) {
  const totalUsers = await env.DB.prepare('SELECT COUNT(*) AS count FROM users').first<{ count: number }>();
  const last7 = await env.DB.prepare(
    "SELECT COALESCE(SUM(searches),0) AS searches, COALESCE(SUM(details),0) AS details, COALESCE(SUM(favorites),0) AS favorites, COALESCE(SUM(new_users),0) AS new_users FROM statistics WHERE date >= date('now','-7 days')"
  ).first<{ searches: number; details: number; favorites: number; new_users: number }>();
  return { totalUsers: totalUsers?.count ?? 0, ...(last7 ?? { searches: 0, details: 0, favorites: 0, new_users: 0 }) };
}

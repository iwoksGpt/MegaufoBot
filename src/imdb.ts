import type { ImdbTitle } from './types';
const BASE_URL = 'https://api.imdbapi.dev';

async function getJson<T>(path: string, params?: Record<string, string | number | string[]>): Promise<T> {
  const url = new URL(path, BASE_URL);
  if (params) for (const [k, v] of Object.entries(params)) Array.isArray(v) ? v.forEach((x) => url.searchParams.append(k, x)) : url.searchParams.set(k, String(v));
  const r = await fetch(url.toString(), { headers: { accept: 'application/json', 'user-agent': 'MegaufoBot/0.3' } });
  if (!r.ok) throw new Error(`IMDbAPI ${r.status}: ${await r.text()}`);
  return r.json<T>();
}
export async function searchTitles(query: string, limit = 20): Promise<ImdbTitle[]> {
  const data = await getJson<{ titles?: ImdbTitle[] }>('/search/titles', { query, limit });
  return data.titles ?? [];
}
export async function getTitle(id: string): Promise<ImdbTitle | null> { try { return await getJson<ImdbTitle>(`/titles/${id}`); } catch { return null; } }
export async function listPopular(type: 'MOVIE' | 'TV_SERIES'): Promise<ImdbTitle[]> {
  const data = await getJson<{ titles?: ImdbTitle[] }>('/titles', { types: [type], sortBy: 'SORT_BY_POPULARITY', sortOrder: 'DESC' });
  return (data.titles ?? []).slice(0, 12);
}
export async function listCredits(titleId: string): Promise<string[]> {
  try {
    const data = await getJson<{ credits?: Array<{ name?: { displayName?: string; nameText?: string } }> }>(`/titles/${titleId}/credits`, { pageSize: 10 });
    return (data.credits ?? []).map((c) => c.name?.displayName ?? c.name?.nameText ?? '').filter(Boolean).slice(0, 8);
  } catch { return []; }
}
export function displayTitle(t: ImdbTitle): string { return t.primaryTitle || t.originalTitle || 'بدون عنوان'; }
export function mediaType(t: ImdbTitle): 'movie' | 'tv' { const v = String(t.type ?? '').toLowerCase(); return v.includes('tv') || v.includes('series') ? 'tv' : 'movie'; }
export function ratingNumber(t: ImdbTitle): string { return t.rating?.aggregateRating ? `${t.rating.aggregateRating}/10` : 'N/A'; }
export function rating(t: ImdbTitle): string { const r = t.rating?.aggregateRating; return r ? `${r}/10` : 'N/A'; }
export function year(t: ImdbTitle): string { return t.startYear ? String(t.startYear) : 'N/A'; }
export function runtime(t: ImdbTitle): string { return t.runtimeMinutes ? `${t.runtimeMinutes} minutes` : 'N/A'; }
export function genres(t: ImdbTitle): string { return t.genres?.length ? t.genres.join(', ') : 'N/A'; }
export function image(t: ImdbTitle): string | undefined { return t.primaryImage?.url; }

import type { ImdbTitle } from './types';

const BASE_URL = 'https://api.imdbapi.dev';

async function getJson<T>(path: string, params?: Record<string, string | number | string[]>): Promise<T> {
  const url = new URL(path, BASE_URL);
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (Array.isArray(value)) value.forEach((item) => url.searchParams.append(key, item));
      else url.searchParams.set(key, String(value));
    }
  }
  const response = await fetch(url.toString(), {
    headers: { accept: 'application/json', 'user-agent': 'MegaufoBot/0.2' }
  });
  if (!response.ok) throw new Error(`IMDbAPI ${response.status}: ${await response.text()}`);
  return response.json<T>();
}

export async function searchTitles(query: string, limit = 8): Promise<ImdbTitle[]> {
  const data = await getJson<{ titles?: ImdbTitle[] }>('/search/titles', { query, limit });
  return data.titles ?? [];
}

export async function getTitle(id: string): Promise<ImdbTitle | null> {
  try {
    return await getJson<ImdbTitle>(`/titles/${id}`);
  } catch {
    return null;
  }
}

export async function listPopular(type: 'MOVIE' | 'TV_SERIES'): Promise<ImdbTitle[]> {
  const data = await getJson<{ titles?: ImdbTitle[] }>('/titles', {
    types: [type],
    sortBy: 'SORT_BY_POPULARITY',
    sortOrder: 'DESC'
  });
  return (data.titles ?? []).slice(0, 10);
}

export async function listCredits(titleId: string): Promise<string[]> {
  try {
    const data = await getJson<{ credits?: Array<{ name?: { displayName?: string; nameText?: string }; category?: string }> }>(`/titles/${titleId}/credits`, { pageSize: 10 });
    return (data.credits ?? [])
      .map((credit) => credit.name?.displayName ?? credit.name?.nameText ?? '')
      .filter(Boolean)
      .slice(0, 8);
  } catch {
    return [];
  }
}

export function displayTitle(title: ImdbTitle): string {
  return title.primaryTitle || title.originalTitle || 'بدون عنوان';
}

export function mediaType(title: ImdbTitle): 'movie' | 'tv' {
  const value = String(title.type ?? '').toLowerCase();
  return value.includes('tv') || value.includes('series') ? 'tv' : 'movie';
}

export function rating(title: ImdbTitle): string {
  const r = title.rating?.aggregateRating;
  const votes = title.rating?.voteCount;
  if (!r) return 'بدون امتیاز';
  return votes ? `${r}/10 از ${votes.toLocaleString('en-US')} رأی` : `${r}/10`;
}

export function year(title: ImdbTitle): string {
  return title.startYear ? String(title.startYear) : 'نامشخص';
}

export function image(title: ImdbTitle): string | undefined {
  return title.primaryImage?.url;
}

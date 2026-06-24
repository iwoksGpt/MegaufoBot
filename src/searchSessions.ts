import type { Env, ImdbTitle } from './types';

export async function createSearchSession(env: Env, userId: number | undefined, query: string, normalizedQuery: string, results: ImdbTitle[]): Promise<string> {
  const id = crypto.randomUUID().replace(/-/g, '').slice(0, 10);
  await env.DB.prepare('INSERT INTO search_sessions (id, user_id, query, normalized_query, results_json, total) VALUES (?, ?, ?, ?, ?, ?)')
    .bind(id, userId ?? null, query, normalizedQuery, JSON.stringify(results), results.length).run();
  return id;
}

export async function getSearchSession(env: Env, id: string): Promise<{ id: string; query: string; normalizedQuery: string; results: ImdbTitle[]; total: number } | null> {
  const row = await env.DB.prepare('SELECT id, query, normalized_query, results_json, total FROM search_sessions WHERE id = ?').bind(id).first<{ id: string; query: string; normalized_query: string; results_json: string; total: number }>();
  if (!row) return null;
  return {
    id: row.id,
    query: row.query,
    normalizedQuery: row.normalized_query,
    results: JSON.parse(row.results_json) as ImdbTitle[],
    total: row.total
  };
}

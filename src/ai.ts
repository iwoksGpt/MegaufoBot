import type { AiMovieDetails, Env, ImdbTitle } from './types';
import { displayTitle, genres, ratingNumber, runtime, year } from './imdb';

type Provider = 'deepseek' | 'openai' | 'xai';

type ProviderConfig = { provider: Provider; key?: string; url: string; model: string };

function baseDetails(title: ImdbTitle): AiMovieDetails {
  return {
    title: displayTitle(title),
    imdbRating: ratingNumber(title),
    rottenTomatoes: 'در حال دریافت...',
    genre: genres(title),
    runtime: runtime(title),
    releaseYear: year(title),
    persianSummary: title.plot || title.description || 'خلاصه داستان در حال آماده‌سازی است...'
  };
}

function promptFor(title: ImdbTitle) {
  return `تو یک نویسنده حرفه‌ای فارسی برای ربات فیلم هستی. فقط JSON معتبر خروجی بده بدون markdown.
اطلاعات فیلم:
Title: ${displayTitle(title)}
Original title: ${title.originalTitle ?? ''}
Year: ${year(title)}
Genres: ${genres(title)}
Runtime: ${runtime(title)}
IMDb: ${ratingNumber(title)}
Existing plot: ${title.plot ?? title.description ?? ''}

JSON schema:
{"title":"Movie Title English","imdbRating":"7.0/10","rottenTomatoes":"72% یا N/A","genre":"Action, Fantasy","runtime":"121 minutes","releaseYear":"2005","persianSummary":"یک خلاصه فارسی جذاب، سینمایی، روان و کوتاه در 5 تا 7 جمله؛ دقیق، هیجان‌انگیز، بدون اسپویلر سنگین."}
اگر Rotten Tomatoes را با اطمینان نمی‌دانی N/A بگذار. از اطلاعات ساختگی قطعی پرهیز کن.`;
}

async function callProvider(config: ProviderConfig, title: ImdbTitle): Promise<AiMovieDetails | null> {
  if (!config.key) return null;
  const response = await fetch(config.url, {
    method: 'POST',
    headers: { 'content-type': 'application/json', authorization: `Bearer ${config.key}` },
    body: JSON.stringify({
      model: config.model,
      messages: [
        { role: 'system', content: 'You output valid JSON only. No markdown fences.' },
        { role: 'user', content: promptFor(title) }
      ],
      temperature: 0.7,
      max_tokens: 700
    })
  });
  if (!response.ok) return null;
  const data = await response.json<any>();
  const content = data.choices?.[0]?.message?.content;
  if (!content) return null;
  const cleaned = String(content).replace(/^```json\s*/i, '').replace(/```$/i, '').trim();
  try {
    const parsed = JSON.parse(cleaned) as Partial<AiMovieDetails>;
    const base = baseDetails(title);
    return {
      title: parsed.title || base.title,
      imdbRating: parsed.imdbRating || base.imdbRating,
      rottenTomatoes: parsed.rottenTomatoes || 'N/A',
      genre: parsed.genre || base.genre,
      runtime: parsed.runtime || base.runtime,
      releaseYear: parsed.releaseYear || base.releaseYear,
      persianSummary: parsed.persianSummary || base.persianSummary
    };
  } catch { return null; }
}

export async function enrichMovie(env: Env, title: ImdbTitle): Promise<{ details: AiMovieDetails; provider: string }> {
  const cached = await env.DB.prepare('SELECT payload_json, provider FROM ai_cache WHERE title_id = ?').bind(title.id).first<{ payload_json: string; provider?: string }>();
  if (cached?.payload_json) {
    try { return { details: JSON.parse(cached.payload_json), provider: cached.provider ?? 'cache' }; } catch {}
  }
  const providers: ProviderConfig[] = [
    { provider: 'deepseek', key: env.DEEPSEEK_API_KEY, url: 'https://api.deepseek.com/chat/completions', model: 'deepseek-chat' },
    { provider: 'openai', key: env.OPENAI_API_KEY, url: 'https://api.openai.com/v1/chat/completions', model: 'gpt-4o-mini' },
    { provider: 'xai', key: env.XAI_API_KEY, url: 'https://api.x.ai/v1/chat/completions', model: 'grok-3-mini' }
  ];
  for (const p of providers) {
    try {
      const details = await callProvider(p, title);
      if (details) {
        await env.DB.prepare('INSERT OR REPLACE INTO ai_cache (title_id, payload_json, provider, updated_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)')
          .bind(title.id, JSON.stringify(details), p.provider).run();
        return { details, provider: p.provider };
      }
    } catch { /* next */ }
  }
  return { details: baseDetails(title), provider: 'fallback' };
}

export function loadingDetails(title: ImdbTitle): AiMovieDetails {
  const base = baseDetails(title);
  return { ...base, rottenTomatoes: '⏳ در حال دریافت...', persianSummary: '⏳ خلاصه داستان با هوش مصنوعی در حال آماده‌سازی است...' };
}

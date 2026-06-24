import type { Env, ImdbTitle } from './types';
import { displayTitle, rating, year } from './imdb';

export type EnrichedMovie = {
  rottenTomatoes?: string;
  summaryFa: string;
};

function stripJson(text: string): string {
  return text.replace(/^```json\s*/i, '').replace(/^```\s*/i, '').replace(/```$/i, '').trim();
}

async function callOpenAICompatible(apiKey: string, url: string, model: string, prompt: string): Promise<EnrichedMovie | null> {
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      authorization: `Bearer ${apiKey}`
    },
    body: JSON.stringify({
      model,
      temperature: 0.65,
      response_format: { type: 'json_object' },
      messages: [
        { role: 'system', content: 'You generate concise Persian movie metadata. Return valid JSON only.' },
        { role: 'user', content: prompt }
      ]
    })
  });
  if (!response.ok) return null;
  const data = await response.json<{ choices?: Array<{ message?: { content?: string } }> }>();
  const content = data.choices?.[0]?.message?.content;
  if (!content) return null;
  try {
    const parsed = JSON.parse(stripJson(content)) as Partial<EnrichedMovie>;
    if (!parsed.summaryFa) return null;
    return {
      rottenTomatoes: parsed.rottenTomatoes || 'نامشخص',
      summaryFa: parsed.summaryFa.slice(0, 900)
    };
  } catch {
    return null;
  }
}

export async function enrichMovie(env: Env, title: ImdbTitle): Promise<EnrichedMovie> {
  const prompt = `برای فیلم/سریال زیر یک خروجی JSON بساز. زبان خروجی فارسی محاوره‌ای، سینمایی و جذاب باشد، شبیه نمونه‌ای که کاربر داده.\n\nقوانین:\n- فقط JSON معتبر بده.\n- rottenTomatoes اگر دقیق نمی‌دانی "نامشخص" بده، درصد جعلی نساز.\n- summaryFa یک خلاصه کوتاه، هیجان‌انگیز و روان فارسی باشد؛ نه خیلی طولانی؛ حدود 90 تا 140 کلمه.\n\nTitle: ${displayTitle(title)}\nOriginal: ${title.originalTitle ?? ''}\nYear: ${year(title)}\nIMDb: ${rating(title)}\nGenres: ${(title.genres ?? []).join(', ')}\nExisting plot: ${title.plot ?? title.description ?? ''}\n\nJSON schema:\n{"rottenTomatoes":"72% یا نامشخص","summaryFa":"..."}`;

  if (env.DEEPSEEK_API_KEY) {
    const result = await callOpenAICompatible(env.DEEPSEEK_API_KEY, 'https://api.deepseek.com/chat/completions', 'deepseek-chat', prompt);
    if (result) return result;
  }
  if (env.OPENAI_API_KEY) {
    const result = await callOpenAICompatible(env.OPENAI_API_KEY, 'https://api.openai.com/v1/chat/completions', 'gpt-4o-mini', prompt);
    if (result) return result;
  }
  if (env.XAI_API_KEY) {
    const result = await callOpenAICompatible(env.XAI_API_KEY, 'https://api.x.ai/v1/chat/completions', 'grok-3-mini', prompt);
    if (result) return result;
  }
  return {
    rottenTomatoes: 'نامشخص',
    summaryFa: title.plot || title.description || 'خلاصه داستان برای این عنوان در دسترس نیست، اما می‌توانی با اطلاعات IMDb، ژانر، سال ساخت و امتیاز آن تصمیم بگیری که تماشایش برایت جذاب هست یا نه.'
  };
}

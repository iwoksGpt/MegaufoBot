export interface Env {
  TELEGRAM_TOKEN: string;
  ADMIN_IDS?: string;
  WEBHOOK_SECRET?: string;
  DEEPSEEK_API_KEY?: string;
  OPENAI_API_KEY?: string;
  XAI_API_KEY?: string;
  DB: D1Database;
}

export type TelegramUpdate = {
  update_id: number;
  message?: TelegramMessage;
  callback_query?: TelegramCallbackQuery;
};

export type TelegramUser = {
  id: number;
  is_bot?: boolean;
  first_name?: string;
  last_name?: string;
  username?: string;
  language_code?: string;
};

export type TelegramChat = { id: number; type: string };

export type TelegramMessage = {
  message_id: number;
  from?: TelegramUser;
  chat: TelegramChat;
  text?: string;
  caption?: string;
};

export type TelegramCallbackQuery = {
  id: string;
  from: TelegramUser;
  message?: TelegramMessage;
  data?: string;
};

export type InlineKeyboardButton = { text: string; callback_data?: string; url?: string };
export type ReplyMarkup = { inline_keyboard?: InlineKeyboardButton[][] };

export type ImdbTitle = {
  id: string;
  type?: string;
  primaryTitle?: string;
  originalTitle?: string;
  primaryImage?: { url?: string; width?: number; height?: number };
  startYear?: number;
  endYear?: number;
  plot?: string;
  description?: string;
  genres?: string[];
  rating?: { aggregateRating?: number; voteCount?: number };
  runtimeMinutes?: number;
  countriesOfOrigin?: string[];
  releaseDate?: string;
};

export type AiMovieDetails = {
  title: string;
  imdbRating: string;
  rottenTomatoes: string;
  genre: string;
  runtime: string;
  releaseYear: string;
  persianSummary: string;
};

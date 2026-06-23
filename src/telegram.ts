import type { InlineKeyboardButton, ReplyMarkup } from './types';

export class TelegramAPI {
  private readonly baseUrl: string;

  constructor(token: string) {
    this.baseUrl = `https://api.telegram.org/bot${token}`;
  }

  private async call<T>(method: string, payload: Record<string, unknown>): Promise<T> {
    const response = await fetch(`${this.baseUrl}/${method}`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await response.json<T & { ok?: boolean; description?: string }>();
    if (!response.ok || data.ok === false) {
      throw new Error(`Telegram ${method} failed: ${data.description ?? response.statusText}`);
    }
    return data;
  }

  sendMessage(chatId: number, text: string, replyMarkup?: ReplyMarkup) {
    return this.call('sendMessage', {
      chat_id: chatId,
      text,
      parse_mode: 'Markdown',
      disable_web_page_preview: true,
      reply_markup: replyMarkup
    });
  }

  sendPhoto(chatId: number, photo: string, caption: string, replyMarkup?: ReplyMarkup) {
    return this.call('sendPhoto', {
      chat_id: chatId,
      photo,
      caption,
      parse_mode: 'Markdown',
      reply_markup: replyMarkup
    });
  }

  editMessageText(chatId: number, messageId: number, text: string, replyMarkup?: ReplyMarkup) {
    return this.call('editMessageText', {
      chat_id: chatId,
      message_id: messageId,
      text,
      parse_mode: 'Markdown',
      disable_web_page_preview: true,
      reply_markup: replyMarkup
    });
  }

  answerCallbackQuery(callbackQueryId: string, text?: string) {
    return this.call('answerCallbackQuery', {
      callback_query_id: callbackQueryId,
      text
    });
  }
}

export function keyboard(rows: InlineKeyboardButton[][]): ReplyMarkup {
  return { inline_keyboard: rows };
}

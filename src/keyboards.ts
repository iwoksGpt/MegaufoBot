import { keyboard } from './telegram';

export function mainMenu() {
  return keyboard([
    [{ text: '🔍 جستجو', callback_data: 'action_search' }, { text: '🌟 محبوب‌ترین‌ها', callback_data: 'popular_menu' }],
    [{ text: '❤️ علاقه‌مندی‌ها', callback_data: 'favorites' }, { text: '❓ راهنما', callback_data: 'help' }]
  ]);
}

export function popularMenu() {
  return keyboard([
    [{ text: '🎬 فیلم‌های محبوب', callback_data: 'popular_movie' }, { text: '📺 سریال‌های محبوب', callback_data: 'popular_tv' }],
    [{ text: '🔙 بازگشت', callback_data: 'home' }]
  ]);
}

export function titleActions(id: string, type: 'movie' | 'tv', favorite: boolean) {
  return keyboard([
    [{ text: favorite ? '💔 حذف از علاقه‌مندی‌ها' : '❤️ افزودن به علاقه‌مندی‌ها', callback_data: `${favorite ? 'unfav' : 'fav'}_${id}` }],
    [{ text: '⭐ امتیازدهی', callback_data: `rate_${type}_${id}` }, { text: '🎭 بازیگران', callback_data: `credits_${id}` }],
    [{ text: '🔙 بازگشت', callback_data: 'home' }]
  ]);
}

export function ratingKeyboard(id: string, type: string) {
  const rows = [];
  for (let start = 1; start <= 10; start += 5) {
    rows.push(Array.from({ length: 5 }, (_, index) => {
      const score = start + index;
      return { text: String(score), callback_data: `rated_${type}_${id}_${score}` };
    }));
  }
  rows.push([{ text: '🔙 بازگشت', callback_data: `details_${type}_${id}` }]);
  return keyboard(rows);
}

export function adminMenu() {
  return keyboard([
    [{ text: '📊 آمار', callback_data: 'admin_stats' }],
    [{ text: '🔙 بازگشت', callback_data: 'home' }]
  ]);
}

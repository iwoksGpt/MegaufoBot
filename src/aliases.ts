export const PERSIAN_TITLE_ALIASES: Record<string, string> = {
  'تلقین': 'Inception',
  'اینسپشن': 'Inception',
  'میان ستاره ای': 'Interstellar',
  'میان‌ستاره‌ای': 'Interstellar',
  'بین ستاره ای': 'Interstellar',
  'شوالیه تاریکی': 'The Dark Knight',
  'بتمن شوالیه تاریکی': 'The Dark Knight',
  'برکینگ بد': 'Breaking Bad',
  'افسارگسیخته': 'Breaking Bad',
  'بازی تاج و تخت': 'Game of Thrones',
  'گیم آف ترونز': 'Game of Thrones',
  'خانه اژدها': 'House of the Dragon',
  'خاندان اژدها': 'House of the Dragon',
  'فرندز': 'Friends',
  'دوستان': 'Friends',
  'ارباب حلقه ها': 'The Lord of the Rings',
  'ارباب حلقه‌ها': 'The Lord of the Rings',
  'هابیت': 'The Hobbit',
  'ماتریکس': 'The Matrix',
  'گلادیاتور': 'Gladiator',
  'رستگاری در شاوشنک': 'The Shawshank Redemption',
  'شاوشنک': 'The Shawshank Redemption',
  'پدرخوانده': 'The Godfather',
  'فارست گامپ': 'Forrest Gump',
  'باشگاه مشت زنی': 'Fight Club',
  'فایت کلاب': 'Fight Club',
  'جوکر': 'Joker',
  'انتقام جویان': 'Avengers',
  'اونجرز': 'Avengers',
  'مرد عنکبوتی': 'Spider-Man',
  'اسپایدرمن': 'Spider-Man',
  'هری پاتر': 'Harry Potter',
  'چرنوبیل': 'Chernobyl',
  'وایکینگ ها': 'Vikings',
  'وایکینگ‌ها': 'Vikings',
  'شرلوک': 'Sherlock',
  'لاست': 'Lost',
  'مردگان متحرک': 'The Walking Dead',
  'واکینگ دد': 'The Walking Dead',
  'چیزهای عجیب': 'Stranger Things',
  'استرنجر تینگز': 'Stranger Things',
  'دارک': 'Dark',
  'ویچر': 'The Witcher',
  'آخرین بازمانده از ما': 'The Last of Us',
  'لست آو آس': 'The Last of Us',
  'اوپنهایمر': 'Oppenheimer',
  'باربی': 'Barbie',
  'تلماسه': 'Dune',
  'دون': 'Dune',
  'انگل': 'Parasite',
  'پارازیت': 'Parasite'
};

export function normalizePersian(input: string): string {
  return input
    .trim()
    .replace(/[ي]/g, 'ی')
    .replace(/[ك]/g, 'ک')
    .replace(/\s+/g, ' ')
    .toLowerCase();
}

export function resolveQueryAlias(query: string): string {
  const normalized = normalizePersian(query);
  return PERSIAN_TITLE_ALIASES[normalized] ?? query.trim();
}

export function persianDisplayName(englishTitle: string): string | undefined {
  const normalizedEnglish = englishTitle.toLowerCase();
  const found = Object.entries(PERSIAN_TITLE_ALIASES).find(([, en]) => en.toLowerCase() === normalizedEnglish);
  return found?.[0];
}

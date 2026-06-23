# MegaufoBot Upgrade Notes

Implemented in the Cloudflare Worker version:

- Stronger admin panel
  - live stats
  - paginated users list
  - user detail page
  - block/unblock users
  - broadcast flow
  - recent search logs
- User profile
  - language selection: Persian / English
  - user stats: messages, searches, favorites, ratings
- Persian + English search
  - alias dictionary for common Persian movie/series names
  - original query + normalized fallback search
- Rich Telegram result cards
  - poster image when available
  - Markdown caption with year, IMDb rating, genre, overview
  - glass-style inline button labels
- Telegram reactions
  - reacts to /start, /help, /profile, /popular, /favorites, /admin and searches
- D1 migration
  - user block status
  - last seen and message count
  - search logs
  - admin sessions for broadcast

Premium emoji note: Telegram premium custom emoji reactions require valid `custom_emoji_id` values and bot/API support. Current implementation uses standard Telegram emoji reactions for reliability.

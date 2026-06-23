# Progressive Movie Details Upgrade

Implemented:

- Search results are now a single Telegram message.
- Search result message includes total result count, page count, and numbered titles.
- Inline buttons show 4 numbered results per page.
- Pagination starts with a single Next button when only next page exists; later pages show Previous/Next as appropriate.
- Movie detail click sends poster with a Persian form-style caption.
- Detail caption starts with loading placeholders, then updates progressively after AI enrichment.
- AI fallback order: DeepSeek -> OpenAI -> xAI -> local IMDb fallback.
- AI keys are Cloudflare Secrets only, never committed.
- Search sessions and AI cache are stored in D1.
- Reactions are applied to user messages for text requests and to bot messages for callback-only actions.

Premium emoji note:
Telegram premium custom emoji requires custom emoji IDs and compatible bot capabilities. The bot currently uses standard emoji reactions and loading symbols for reliability.

# Cloudflare deploy checklist

1. `npm install`
2. `npx wrangler login`
3. `npx wrangler d1 create megaufobot-db`
4. Put returned `database_id` in `wrangler.jsonc`
5. `npm run db:migrate:remote`
6. `npx wrangler secret put TELEGRAM_TOKEN`
7. `npx wrangler secret put ADMIN_IDS` → `YOUR_TELEGRAM_NUMERIC_ID`
8. `npx wrangler secret put WEBHOOK_SECRET`
9. `npm run deploy`
10. `TELEGRAM_TOKEN=... WORKER_URL=... WEBHOOK_SECRET=... npm run set-webhook`

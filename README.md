# MegaufoBot — Cloudflare Telegram Bot

Cloudflare Worker + TypeScript + D1 Telegram bot using the free IMDb API at `https://imdbapi.dev/`.

## Features

- Telegram webhook; no polling process needed
- IMDb title search
- Movie/TV detail cards
- Favorites stored in Cloudflare D1
- User ratings stored in D1
- Admin stats panel
- Secure secrets via Cloudflare Secrets

## Setup

### 1. Install dependencies

```bash
npm install
```

### 2. Create D1 database

```bash
npx wrangler d1 create megaufobot-db
```

Copy the returned `database_id` into `wrangler.jsonc` in place of:

```text
REPLACE_WITH_D1_DATABASE_ID
```

### 3. Apply migrations

```bash
npm run db:migrate:remote
```

For local development:

```bash
npm run db:migrate:local
```

### 4. Set Cloudflare secrets

```bash
npx wrangler secret put TELEGRAM_TOKEN
npx wrangler secret put ADMIN_IDS
npx wrangler secret put WEBHOOK_SECRET
```

Use your admin ID for `ADMIN_IDS`:

```text
YOUR_TELEGRAM_NUMERIC_ID
```

`WEBHOOK_SECRET` should be a random string used in the webhook path.

### 5. Deploy

```bash
npm run deploy
```

### 6. Register Telegram webhook

After deploy, set:

```bash
export TELEGRAM_TOKEN='YOUR_BOT_TOKEN'
export WORKER_URL='https://megaufobot.YOUR_SUBDOMAIN.workers.dev'
export WEBHOOK_SECRET='same-secret-you-set-in-cloudflare'
npm run set-webhook
```

Health check:

```text
https://megaufobot.YOUR_SUBDOMAIN.workers.dev/health
```

## Local dev

Create `.dev.vars` from `.dev.vars.example` and put your local secrets there.

```bash
cp .dev.vars.example .dev.vars
npm run db:migrate:local
npm run dev
```

Then use a tunnel or deployed worker for Telegram webhook testing.

## Security

Never commit Telegram bot token. Use Cloudflare Secrets and local `.dev.vars` only.

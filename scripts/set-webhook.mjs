const token = process.env.TELEGRAM_TOKEN;
const workerUrl = process.env.WORKER_URL;
const secret = process.env.WEBHOOK_SECRET || 'telegram';
if (!token || !workerUrl) {
  console.error('Usage: TELEGRAM_TOKEN=... WORKER_URL=https://your-worker.workers.dev WEBHOOK_SECRET=... npm run set-webhook');
  process.exit(1);
}
const url = `${workerUrl.replace(/\/$/, '')}/webhook/${secret}`;
const api = `https://api.telegram.org/bot${token}/setWebhook?url=${encodeURIComponent(url)}`;
const res = await fetch(api);
console.log(await res.text());

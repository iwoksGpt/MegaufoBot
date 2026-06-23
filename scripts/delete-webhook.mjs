const token = process.env.TELEGRAM_TOKEN;
if (!token) {
  console.error('Usage: TELEGRAM_TOKEN=... npm run delete-webhook');
  process.exit(1);
}
const res = await fetch(`https://api.telegram.org/bot${token}/deleteWebhook`);
console.log(await res.text());

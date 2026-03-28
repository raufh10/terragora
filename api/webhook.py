import asyncio
import httpx
from services.config import configs

BOT_TOKEN = configs.telegram_bot_token.get_secret_value()
WEBHOOK_URL = configs.telegram_webhook_url.get_secret_value()
WEBHOOK_SECRET = configs.telegram_webhook_secret.get_secret_value()

API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"

async def delete_webhook(client):
  res = await client.post(f"{API_BASE}/deleteWebhook")
  print("🧹 deleteWebhook:", res.json())

async def set_webhook(client):
  res = await client.post(f"{API_BASE}/setWebhook", data={
    "url": WEBHOOK_URL,
    "secret_token": WEBHOOK_SECRET
  })
  print("🔐 setWebhook:", res.json())

async def get_webhook_info(client):
  res = await client.get(f"{API_BASE}/getWebhookInfo")
  print("🔍 getWebhookInfo:", res.json())

async def main():
  async with httpx.AsyncClient(timeout=10.0) as client:
    await delete_webhook(client)
    await set_webhook(client)
    await get_webhook_info(client)

if __name__ == "__main__":
  asyncio.run(main())

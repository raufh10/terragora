import os
import httpx
import asyncio

from dotenv import load_dotenv
load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("TELEGRAM_WEBHOOK_URL")
WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET")

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
  # Basic validation to ensure variables aren't None
  if not all([BOT_TOKEN, WEBHOOK_URL, WEBHOOK_SECRET]):
    print("❌ Error: One or more environment variables are missing in .env")
    return

  async with httpx.AsyncClient(timeout=10.0) as client:
    await delete_webhook(client)
    await set_webhook(client)
    await get_webhook_info(client)

if __name__ == "__main__":
  asyncio.run(main())

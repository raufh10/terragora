import httpx
import asyncio
from fastapi import FastAPI, Request
from services.config import configs
from services import reply

app = FastAPI()

BOT_TOKEN = configs.telegram_bot_token.get_secret_value()
API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"

client = httpx.AsyncClient()

async def send_typing(chat_id: int):
  await client.post(f"{API_BASE}/sendChatAction", json={
    "chat_id": chat_id,
    "action": "typing"
  })

async def typing_loop(chat_id: int):
  while True:
    await send_typing(chat_id)
    await asyncio.sleep(4)

@app.post("/webhook")
async def telegram_webhook(request: Request):
  data = await request.json()
  message = data.get("message", {})
  chat_id = message.get("chat", {}).get("id")

  if not chat_id:
    return {"status": "no_chat_id"}

  typing_task = asyncio.create_task(typing_loop(chat_id))

  try:
    reply_text = await reply.get_marketplace_reply(message)

    await client.post(f"{API_BASE}/sendMessage", json={
      "chat_id": chat_id,
      "text": reply_text,
      "parse_mode": "Markdown"
    })

  except Exception as e:
    print(f"❌ Telegram Delivery Error: {e}")

  finally:
    typing_task.cancel()

  return {"status": "ok"}

@app.on_event("shutdown")
async def shutdown_event():
  await client.aclose()

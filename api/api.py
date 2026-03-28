import httpx
import asyncio
from fastapi import FastAPI, Request
from services.config import configs
from services import reply

app = FastAPI()

BOT_TOKEN = configs.telegram_bot_token.get_secret_value()
API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"
WEBHOOK_SECRET = configs.telegram_webhook_secret.get_secret_value()

client = httpx.AsyncClient(timeout=10.0)

last_seen = {}

async def send_typing(chat_id: int):
  await client.post(f"{API_BASE}/sendChatAction", json={
    "chat_id": chat_id,
    "action": "typing"
  })

async def typing_loop(chat_id: int):
  while True:
    await send_typing(chat_id)
    await asyncio.sleep(5)

async def send_message(chat_id: int, text: str):
  await client.post(f"{API_BASE}/sendMessage", json={
    "chat_id": chat_id,
    "text": text
  })

@app.post("/webhook")
async def telegram_webhook(request: Request):
  # ✅ Verify Telegram secret header
  if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != WEBHOOK_SECRET:
    return {"status": "unauthorized"}

  data = await request.json()
  message = data.get("message", {})
  chat_id = message.get("chat", {}).get("id")

  if not chat_id:
    return {"status": "no_chat_id"}

  # =========================
  # ✅ Structured input safety
  # =========================
  text = message.get("text")

  # ❌ Non-text
  if not text:
    await send_message(chat_id, "❌ I only support text messages for now.")
    return {"status": "ignored_non_text"}

  # 🧼 Normalize
  text = text.strip()

  # ❌ Empty
  if not text:
    await send_message(chat_id, "⚠️ Message is empty. Please send something.")
    return {"status": "empty_text"}

  # 📏 Length constraints
  MAX_LEN = 1000
  MIN_LEN = 1

  if len(text) < MIN_LEN:
    await send_message(chat_id, "⚠️ Message too short.")
    return {"status": "too_short"}

  if len(text) > MAX_LEN:
    text = text[:MAX_LEN]
    await send_message(chat_id, "⚠️ Message too long. Truncated to 1000 characters.")

  # 🧠 Normalize whitespace
  text = " ".join(text.split())

  # 🚫 Simple spam guard (optional but useful)
  if text.count("http") > 3:
    await send_message(chat_id, "🚫 Too many links in message.")
    return {"status": "spam_detected"}

  # =========================
  # ✅ Rate limiting
  # =========================
  now = asyncio.get_event_loop().time()
  if chat_id in last_seen and now - last_seen[chat_id] < 1:
    await send_message(chat_id, "⏳ You're sending messages too fast. Please slow down.")
    return {"status": "rate_limited"}

  last_seen[chat_id] = now

  typing_task = asyncio.create_task(typing_loop(chat_id))

  try:
    await asyncio.sleep(2)

    reply_text = await reply.get_marketplace_reply({
      **message,
      "text": text
    })

    await client.post(f"{API_BASE}/sendMessage", json={
      "chat_id": chat_id,
      "text": reply_text,
      "parse_mode": "Markdown"
    })

  except Exception as e:
    print(f"❌ Telegram Delivery Error: {e}")
    await send_message(chat_id, "⚠️ Something went wrong. Please try again.")

  finally:
    typing_task.cancel()

  return {"status": "ok"}

@app.on_event("shutdown")
async def shutdown_event():
  await client.aclose()

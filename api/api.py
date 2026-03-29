import httpx
import asyncio
from fastapi import FastAPI, Request
from services import reply
from services.config import configs
from services.logging import logger

app = FastAPI()

BOT_TOKEN = configs.telegram_bot_token.get_secret_value()
API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"
WEBHOOK_SECRET = configs.telegram_webhook_secret.get_secret_value()

client = httpx.AsyncClient(timeout=10.0)

last_seen = {}

async def send_typing(chat_id: int):
  try:
    await client.post(f"{API_BASE}/sendChatAction", json={
      "chat_id": chat_id,
      "action": "typing"
    })
  except Exception as e:
    logger.error(f"Failed to send typing action: {e}")

async def typing_loop(chat_id: int):
  try:
    while True:
      await send_typing(chat_id)
      await asyncio.sleep(4)
  except asyncio.CancelledError:
    pass

async def send_message(chat_id: int, text: str):
  try:
    await client.post(f"{API_BASE}/sendMessage", json={
      "chat_id": chat_id,
      "text": text
    })
  except Exception as e:
    logger.error(f"Failed to send alert message to user: {e}")

@app.post("/webhook")
async def telegram_webhook(request: Request):
  # ✅ Verify Telegram secret header
  if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != WEBHOOK_SECRET:
    logger.warning("Unauthorized webhook access attempt.")
    return {"status": "unauthorized"}

  data = await request.json()
  message = data.get("message", {})
  chat_id = message.get("chat", {}).get("id")
  user = message.get("from", {}).get("username", "Unknown")

  if not chat_id:
    return {"status": "no_chat_id"}

  text = message.get("text")

  # ❌ Non-text handling
  if not text:
    logger.info(f"Non-text from @{user}")
    await send_message(chat_id, "❌ I only support text messages for now.")
    return {"status": "ignored_non_text"}

  # 🧼 Normalize
  text = text.strip()

  # ❌ Empty check
  if not text:
    return {"status": "empty_text"}

  # 📏 Constraints
  if len(text) > 1000:
    text = text[:1000]

  # 🧠 Normalize whitespace
  text = " ".join(text.split())

  # 🚫 Spam guard
  if text.count("http") > 3:
    logger.warning(f"Spam filter triggered by @{user}")
    await send_message(chat_id, "🚫 Too many links in message.")
    return {"status": "spam_detected"}

  # =========================
  # ✅ Rate limiting
  # =========================
  now = asyncio.get_event_loop().time()
  if chat_id in last_seen and now - last_seen[chat_id] < 1:
    logger.debug(f"Rate limit hit: @{user}")
    await send_message(chat_id, "⏳ You're sending messages too fast. Please slow down.")
    return {"status": "rate_limited"}

  last_seen[chat_id] = now

  # ✅ Notify on incoming message only
  logger.info(f"📥 Incoming: @{user} -> {text[:60]}...", extra={"notify": True})

  typing_task = asyncio.create_task(typing_loop(chat_id))

  try:
    await asyncio.sleep(0.5)

    reply_text = await reply.get_marketplace_reply({
      **message,
      "text": text
    })

    await client.post(f"{API_BASE}/sendMessage", json={
      "chat_id": chat_id,
      "text": reply_text,
      "parse_mode": "Markdown"
    })
    
    logger.info(f"📤 Reply sent to @{user}")

  except Exception as e:
    logger.error(f"🔥 Telegram Delivery Error: {e}", exc_info=True)
    await send_message(chat_id, "⚠️ Something went wrong. Please try again.")

  finally:
    typing_task.cancel()

  return {"status": "ok"}

@app.on_event("shutdown")
async def shutdown_event():
  logger.info("Shutting down bot client...")
  await client.aclose()

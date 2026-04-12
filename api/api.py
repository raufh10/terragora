import httpx
from fastapi import FastAPI, Request
from services.config import configs
from services import reply

app = FastAPI()
TELEGRAM_URL = configs.telegram_url.get_secret_value()

@app.post("/webhook")
async def telegram_webhook(request: Request):
  data = await request.json()
  message = data.get("message", {})
  chat_id = message.get("chat", {}).get("id")

  if not chat_id:
    return {"status": "no_chat_id"}

  reply_text = await reply.get_marketplace_reply(message)

  async with httpx.AsyncClient() as client:
    try:
      await client.post(TELEGRAM_URL, json={
        "chat_id": chat_id,
        "text": reply_text,
        "parse_mode": "Markdown"
      })
    except Exception as e:
      print(f"❌ Telegram Delivery Error: {e}")

  return {"status": "ok"}

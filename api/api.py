import httpx
from fastapi import FastAPI, Request
from services import config, reply

app = FastAPI()

@app.post("/webhook")
async def telegram_webhook(request: Request):
  data = await request.json()
  message = data.get("message", {})
  chat_id = message.get("chat", {}).get("id")

  if not chat_id:
    return {"status": "no_chat_id"}

  reply_text = reply.get_echo_text(message)

  async with httpx.AsyncClient() as client:
    await client.post(config.configs.telegram_url.get_secret_value(), json={
      "chat_id": chat_id,
      "text": reply_text,
      "parse_mode": "Markdown"
    })

  return {"status": "ok"}

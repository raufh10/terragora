def get_echo_text(message_data: dict):
  user_text = message_data.get("text", "").strip()
  if not user_text:
    return "⚠️ Please send some text."
  
  return f"🔄 **Echo:** {user_text}"

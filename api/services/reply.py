from services.pg import get_db_connection, fetch_relevant_posts
from services.llm import get_embedding, search_used_items
from services.messages import format_telegram_message

async def get_marketplace_reply(message_data: dict):

  user_query = message_data.get("text", "").strip()
  if not user_query:
    return "⚠️ What used item are you looking for today?"

  # 🔍 Embedding
  query_vector = await get_embedding(user_query)
  if not query_vector:
    return "❌ Sorry, I had trouble processing your search. Please try again."

  # 🗄️ Fetch from DB
  try:
    with get_db_connection() as conn:
      relevant_posts = fetch_relevant_posts(conn, query_vector, limit=5)
  except Exception as e:
    print(f"DB Error: {e}")
    return "❌ Database connection issue. Please try again later."

  if not relevant_posts:
    return "🔍 No matching items found. Try a different keyword!"

  # 🧠 LLM Analysis
  result = await search_used_items(user_query, relevant_posts)
  if not result or not result.listings:
    return "❌ Failed to analyze results. Try a more specific search."

  # 🧾 Format final Telegram message
  try:
    reply = format_telegram_message(
      user_query=user_query,
      result=result,
      relevant_posts=relevant_posts
    )
    return reply

  except Exception as e:
    print(f"Format Error: {e}")
    return "❌ Error formatting results. Please try again."

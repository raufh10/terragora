from services.pg import get_db_connection, fetch_relevant_posts
from services.llm import get_embedding, search_used_items

async def get_marketplace_reply(message_data: dict):

  user_query = message_data.get("text", "").strip()
  if not user_query:
    return "⚠️ What used item are you looking for today?"

  query_vector = await get_embedding(user_query)
  if not query_vector:
    return "❌ Sorry, I had trouble processing your search. Please try again."

  try:
    with get_db_connection() as conn:
      relevant_posts = fetch_relevant_posts(conn, query_vector, limit=5)
  except Exception as e:
    print(f"DB Error: {e}")
    return "❌ Database connection issue. Please try again later."

  if not relevant_posts:
    return "🔍 No matching items found in the database. Try a different keyword!"

  result = await search_used_items(user_query, relevant_posts)
  if not result:
    return "❌ Failed to analyze the results. Please try a more specific search."

  reply = f"📦 **Marketplace Results for:** _{user_query}_\n\n"
  reply += f"{result.summary}\n\n"
  reply += f"💡 **Recommendation:** {result.recommendation}\n\n"
  
  if result.best_deal_url:
    best_item = next((p for p in relevant_posts if str(p['metadata']['url']) == result.best_deal_url), None)
    if best_item:
      reply += f"🏆 **Top Pick:** {best_item['title']}\n"
      if best_item.get('price'):
        reply += f"💰 **Price:** {best_item['price']}\n"

      item_url = best_item.get('metadata', {}).get('url')
      if item_url:
        reply += f"🔗 **Link:** {item_url}\n"

  return reply

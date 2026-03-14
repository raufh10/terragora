from typing import List, Optional
from openai import OpenAI
from pydantic import BaseModel, Field
from services.config import configs

client = OpenAI(api_key=configs.openai_api_key.get_secret_value())

class MarketplaceSearch(BaseModel):
  summary: str = Field(description="A brief summary of available items found matching the user's request.")
  best_deal_id: Optional[str] = Field(description="The UUID of the post with the best price or condition.")
  recommendation: str = Field(description="Advice to the buyer (e.g., 'Check the seller notes for shipping').")

async def get_embedding(text: str) -> List[float]:
  try:
    response = client.embeddings.create(
      input=text,
      model="text-embedding-3-small",
      dimensions=1536
    )
    return response.data[0].embedding
  except Exception:
    return []

async def search_used_items(user_query: str, relevant_posts: List[dict]) -> Optional[MarketplaceSearch]:

  if not relevant_posts:
    return None

  context_entries = []
  for p in relevant_posts:
    entry = (
      f"Item: {p['title']}\n"
      f"Description: {p['content']}\n"
      f"Price: {p.get('price', 'N/A')}\n"
      f"url: {p.get('metadata', {}).get('url', '')}"
    )
    context_entries.append(entry)
  
  context_text = "\n\n---\n\n".join(context_entries)

  try:
    completion = client.beta.chat.completions.parse(
      model="gpt-5-mini-2025-08-07",
      messages=[
        {
          "role": "system", 
          "content": (
            "You are a marketplace assistant for used items. "
            "Analyze the provided Reddit posts to find the best matches for the user. "
            "Focus on price, item condition, and seller credibility mentioned in the notes."
          )
        },
        {"role": "user", "content": f"User Search: {user_query}\n\nContext:\n{context_text}"},
      ],
      response_format=MarketplaceSearch,
    )
    return completion.choices[0].message.parsed
  except Exception as e:
    print(f"❌ LLM Error: {e}")
    return None

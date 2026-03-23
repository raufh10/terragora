import asyncio
from typing import List, Optional, Annotated
from openai import OpenAI
from pydantic import BaseModel, Field
from services.config import configs

MAX_RETRIES = 2
RETRY_DELAY = 1

client = OpenAI(api_key=configs.openai_api_key.get_secret_value())

ShortStr = Annotated[str, Field(max_length=280)]

class MarketplaceSearch(BaseModel):
  summary: ShortStr = Field(
    description="A summary of matching items found. Strictly maximum 2 sentences."
  )
  best_deal_url: Optional[str] = Field(
    description="The URL of the post identified as the best deal."
  )
  recommendation: ShortStr = Field(
    description="Buying advice or seller warnings. Strictly maximum 2 sentences."
  )

async def get_embedding(text: str) -> List[float]:
  for attempt in range(MAX_RETRIES):
    try:
      response = client.embeddings.create(
        input=text,
        model="text-embedding-3-small",
        dimensions=1536
      )
      return response.data[0].embedding
    except Exception as e:
      print(f"⚠️ Embedding failed (attempt {attempt+1}): {e}")
      if attempt < MAX_RETRIES - 1:
        await asyncio.sleep(RETRY_DELAY)
      else:
        return []

async def search_used_items(user_query: str, relevant_posts: List[dict]) -> Optional[MarketplaceSearch]:
  if not relevant_posts:
    return None

  context_entries = []
  for p in relevant_posts:
    post_url = p.get('metadata', {}).get('url', p.get('url', 'No URL available'))
    entry = (
      f"Item: {p.get('title', 'N/A')}\n"
      f"Description: {p.get('content', 'N/A')}\n"
      f"Price: {p.get('price', 'N/A')}\n"
      f"URL: {post_url}"
    )
    context_entries.append(entry)

  context_text = "\n\n---\n\n".join(context_entries)

  for attempt in range(MAX_RETRIES):
    try:
      response = client.responses.parse(
        model="gpt-5.4-nano-2026-03-17",
        input=[
          {
            "role": "system", 
            "content": (
              "You are a marketplace scout. Analyze the posts to find items for sale. "
              "IMPORTANT: Ignore 'WTB' (Want To Buy) posts; only consider 'WTS' (Want To Sell). "
              "Your summary and recommendation must be extremely concise, maximum 2 sentences each."
            )
          },
          {"role": "user", "content": f"User Search: {user_query}\n\nContext:\n{context_text}"},
        ],
        text_format=MarketplaceSearch,
        prompt_cache_key="marketplace-search-v1",
        prompt_cache_retention="24h"
      )
      return response.output_parsed

    except Exception as e:
      print(f"⚠️ Search analysis failed (attempt {attempt+1}): {e}")
      if attempt < MAX_RETRIES - 1:
        await asyncio.sleep(RETRY_DELAY)
      else:
        print(f"❌ LLM Error: {e}")
        return None

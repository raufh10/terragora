import asyncio
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import List, Optional, Annotated

from services.config import configs
from services.utils import format_price

MAX_RETRIES = 2
RETRY_DELAY = 1

client = OpenAI(api_key=configs.openai_api_key.get_secret_value())

ShortStr = Annotated[str, Field(max_length=280)]

class Listing(BaseModel):
  location: Optional[ShortStr] = Field(
    default=None,
    description="City where the item is located."
  )
  condition: ShortStr = Field(
    description="Condition of the item (e.g., 90%, like new, etc.)."
  )
  seller_notes: List[ShortStr] = Field(
    description="Key bullet points from seller notes (max 3).",
    max_items=3
  )
  verdict: ShortStr = Field(
    description="Clear recommendation label (e.g., Best balance, Budget pick, Premium option)."
  )
  watch_out: ShortStr = Field(
    description="Risk or warning. Use '-' if none."
  )
  deal_score: Optional[float] = Field(
    default=None,
    description="Optional score from 0–10 representing deal quality."
  )
  url: str = Field(
    description="Direct link to the listing."
  )

class MarketplaceSearch(BaseModel):
  listings: List[Listing] = Field(
    description="Top matching listings sorted by relevance."
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

async def search_used_items(
  user_query: str,
  relevant_posts: List[dict]
) -> Optional[MarketplaceSearch]:

  if not relevant_posts:
    return None

  context_entries = []
  for p in relevant_posts:
     price = p.get('price')
     price_line = format_price(price)

    entry = (
      f"Item: {p.get('title', 'N/A')}\n"
      f"Description: {p.get('content', 'N/A')}\n"
      f"Price: {price_line}\n"
    )
    context_entries.append(entry)

  context_text = "\n\n---\n\n".join(context_entries)

  for attempt in range(MAX_RETRIES):
    try:
      response = client.responses.parse(
        model="gpt-5.4-mini-2026-03-17",
        input=[
          {
            "role": "system", 
            "content": configs.MarketplaceSearchPrompt
          },
          {"role": "user", "content": f"User Search: {user_query}\n\nContext:\n{context_text}"},
        ],
        text_format=MarketplaceSearch,
        text={
          "verbosity": "low"
        },
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

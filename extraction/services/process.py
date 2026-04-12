from __future__ import annotations
from typing import List, Dict, Any, Optional
from services.config import configs
from pydantic import BaseModel
from openai import OpenAI

client = OpenAI(api_key=configs.openai_api_key.get_secret_value())

class ItemExtraction(BaseModel):
  item_name: str
  price: Optional[float]
  category: str
  currency: str = "IDR"

async def get_embedding(text: str) -> List[float]:
  try:
    response = client.embeddings.create(
      input=text,
      model="text-embedding-3-small"
    )
    return response.data[0].embedding
  except Exception:
    return []

async def process_submissions(submissions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
  processed_results = []

  for post in submissions:

    combined_text = (
      f"Title: {post.get('title', '')}\n"
      f"Flair: {post.get('link_flair_text', '')}\n"
      f"Content: {post.get('selftext', '')}"
    )

    try:
      response = client.beta.chat.completions.parse(
        model="gpt-5-nano-2025-08-07",
        messages=[
          {
            "role": "system",
            "content": "Extract item name, price, and category. If price is not mentioned, return null."
          },
          {"role": "user", "content": combined_text},
        ],
        response_format=ItemExtraction,
      )

      extracted = response.choices[0].message.parsed

      embedding = await get_embedding(combined_text)

      result = {
        "id": post.get("id"),
        "permalink": post.get("permalink"),
        "extracted_data": extracted.model_dump(),
        "embedding": embedding
      }
      processed_results.append(result)

    except Exception:
      continue

  return processed_results


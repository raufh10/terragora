from __future__ import annotations
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from openai import OpenAI

client = OpenAI()

class ItemExtraction(BaseModel):
  item_name: str
  price: Optional[float]
  category: str
  currency: str = "IDR"

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
      
      result = {
        "id": post.get("id"),
        "permalink": post.get("permalink"),
        "extracted_data": extracted.dict()
      }
      processed_results.append(result)

    except Exception:
      continue

  return processed_results

import asyncio
from openai import OpenAI
from typing import List, Optional
from services.config import configs
from services.models import ProductExtraction

client = OpenAI(api_key=configs.openai_api_key.get_secret_value())

async def get_embedding(text: str) -> List[float]:
  for attempt in range(configs.MAX_RETRIES):
    try:
      response = client.embeddings.create(
        input=text,
        model="text-embedding-3-small",
        dimensions=1536
      )
      return response.data[0].embedding

    except Exception as e:
      print(f"⚠️ Embedding failed (attempt {attempt+1}): {e}")
      if attempt < configs.MAX_RETRIES - 1:
        await asyncio.sleep(configs.RETRY_DELAY)
      else:
        print("❌ Embedding failed after retries")
        return []

async def extract_product_details(text: str) -> Optional[ProductExtraction]:
  for attempt in range(configs.MAX_RETRIES):
    try:
      response = client.responses.parse(
        model="gpt-5.4-nano-2026-03-17",
        input=[
          {
            "role": "system", 
            "content": configs.ProductExtractionPrompt
          },
          {
            "role": "user", 
            "content": text
          },
        ],
        text_format=ProductExtraction,
        prompt_cache_key="leaddits-productparser-0.1",
        prompt_cache_retention="24h"
      )

      return response.output_parsed

    except Exception as e:
      print(f"⚠️ Product extraction failed (attempt {attempt+1}): {e}")
      if attempt < configs.MAX_RETRIES - 1:
        await asyncio.sleep(configs.RETRY_DELAY)
      else:
        print(f"❌ Product extraction failed after {configs.MAX_RETRIES} attempts")
        return None

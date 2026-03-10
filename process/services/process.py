from typing import List, Optional
from openai import OpenAI
from pydantic import BaseModel, Field
from services.config import configs

client = OpenAI(api_key=configs.openai_api_key.get_secret_value())

class ProductExtraction(BaseModel):
  prices: List[float] = Field(description="Numerical prices extracted from the text.")
  notes: str = Field(description="1-3 sentences of additional context regarding condition, location, or bundle details.")

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

async def extract_product_details(text: str) -> Optional[ProductExtraction]:
  try:
    completion = client.beta.chat.completions.parse(
      model="gpt-5-nano-2025-08-07",
      messages=[
        {"role": "system", "content": "Extract pricing and 1-3 sentences of seller notes from the marketplace post with high precision."},
        {"role": "user", "content": text},
      ],
      response_format=ProductExtraction,
    )
    return completion.choices[0].message.parsed
  except Exception as e:
    print(f"❌ Error during structured extraction: {e}")
    return None

import re
from typing import Type
from pydantic import BaseModel

def clean_text(text: str) -> str:
  if not text:
    return ""
  text = re.sub(r'http\S+', '', text)
  text = re.sub(r'\[.*?\]', '', text)
  return " ".join(text.split())

def extract_category(metadata: dict) -> str:
  try:
    flair_list = metadata.get("link_flair_richtext", [])

    if flair_list and isinstance(flair_list, list):
      category = " ".join([item.get("t", "") for item in flair_list if item.get("e") == "text"])
      return category.strip()

  except Exception:
    pass
  return "General"

def assemble_embedding_text(title: str, price: float, notes: str, category: str) -> str:
  price_str = f"Rp{price:,.0f}" if price else "Price N/A"
  return f"Category: {category} | Product: {title} | Price: {price_str} | Info: {notes}"

def format_payloads(processed_results: list):
  price_updates = []
  embedding_updates = []
  
  for item in processed_results:
    if item['price'] is not None:
      price_updates.append((item['price'], item['id']))
    if item['embedding']:
      embedding_updates.append((item['embedding'], item['id']))
      
  return price_updates, embedding_updates

def build_openai_text_format(model_class: Type[BaseModel], schema_name: str) -> dict:

  schema = model_class.model_json_schema()
  schema["required"] = list(schema["properties"].keys())
  schema["additionalProperties"] = False

  return {
    "format": {
      "type": "json_schema",
      "name": schema_name,
      "strict": True,
      "schema": schema
    }
  }

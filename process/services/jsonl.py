import json
from datetime import datetime
from typing import List, Type
from pydantic import BaseModel
from services.utils import build_openai_text_format

def generate_embedding_jsonl(
  texts: List[str], 
  model: str = "text-embedding-3-small", 
  dimensions: int = 1536
) -> str:
  date_str = datetime.now().strftime("%Y%m%d")
  lines = []
  for i, text in enumerate(texts):
    line = {
      "custom_id": f"leaddits-embed-{date_str}-{i}",
      "method": "POST",
      "url": "/v1/embeddings",
      "body": {
        "model": model,
        "input": text,
        "dimensions": dimensions
      }
    }
    lines.append(json.dumps(line))

  return "\n".join(lines)

def generate_structured_jsonl(
  texts: List[str], 
  system_prompt: str, 
  model_class: Type[BaseModel], 
  schema_name: str,
  model: str = "gpt-5.4-nano-2026-03-17"
) -> str:
  date_str = datetime.now().strftime("%Y%m%d")
  text_format_config = build_openai_text_format(model_class, schema_name)

  lines = []
  for i, text in enumerate(texts):
    line = {
      "custom_id": f"leaddits-process-{date_str}-{i}",
      "method": "POST",
      "url": "/v1/responses",
      "body": {
        "model": model,
        "input": [
          {"role": "system", "content": system_prompt},
          {"role": "user", "content": text}
        ],
        "text": text_format_config["format"]
      }
    }
    lines.append(json.dumps(line))

  return "\n".join(lines)

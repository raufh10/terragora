import json
from datetime import datetime
from typing import List, Type
from pydantic import BaseModel
from services.utils import build_openai_text_format

def generate_embedding_jsonl(
  texts: List[dict], 
  model: str = "text-embedding-3-small", 
  dimensions: int = 1536
) -> str:
  date_str = datetime.now().strftime("%Y%m%d")
  lines = []
  for text in texts:

    line = {
      "custom_id": f"leaddits-embed-{date_str}-{text["id"]}",
      "method": "POST",
      "url": "/v1/embeddings",
      "body": {
        "model": model,
        "input": text["text"],
        "dimensions": dimensions
      }
    }
    lines.append(json.dumps(line))

  return "\n".join(lines)

def generate_structured_jsonl(
  texts: List[dict], 
  system_prompt: str, 
  model_class: Type[BaseModel], 
  schema_name: str,
  model: str = "gpt-5.4-nano-2026-03-17"
) -> str:
  date_str = datetime.now().strftime("%Y%m%d")
  text_format_config = build_openai_text_format(model_class, schema_name)

  lines = []
  for text in texts:
    line = {
      "custom_id": f"leaddits-process-{date_str}-{text["id"]}",
      "method": "POST",
      "url": "/v1/responses",
      "body": {
        "model": model,
        "input": [
          {"role": "system", "content": system_prompt},
          {"role": "user", "content": text["text"]}
        ],
        "text": text_format_config
      }
    }
    lines.append(json.dumps(line))

  return "\n".join(lines)

def extract_batch_embeddings(content: str) -> dict:

  embeddings_map = {}
  
  for line in content.splitlines():
    if not line.strip(): 
      continue
    try:
      obj = json.loads(line)
      custom_id = obj.get("custom_id")
      
      response_body = obj.get("response", {}).get("body", {})
      data_array = response_body.get("data", [])

      if data_array:
        vector = data_array[0].get("embedding")
        if vector and custom_id:
          embeddings_map[custom_id] = vector
    except Exception as e:
      print(f"❌ Error parsing embedding line: {e}")

  return embeddings_map

def process_batch_output(content: str) -> dict:

  text_map = {}
  
  for line in content.splitlines():
    if not line.strip(): 
      continue
    try:
      obj = json.loads(line)
      custom_id = obj.get("custom_id")
      
      response_body = obj.get("response", {}).get("body", {})
      
      output_list = response_body.get("output")
      if output_list and len(output_list) > 0:
        content_list = output_list[0].get("content")
        if content_list and len(content_list) > 0:
          output_text = content_list[0].get("text")
          
          if output_text and custom_id:
            text_map[custom_id] = output_text
    except Exception as e:
      print(f"❌ Error parsing text line: {e}")

  return text_map


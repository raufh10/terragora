import os
import tempfile

from pydantic import BaseModel
from typing import List, Type, Dict, Any

from openai import OpenAI

from services.config import configs
from services.pg import get_db_connection, insert_batch
from services.jsonl import generate_embedding_jsonl, generate_structured_jsonl
from services.llm import create_batch_file, create_structured_batch_job, create_embedding_batch_job

client = OpenAI(api_key=configs.openai_api_key.get_secret_value())

async def orchestrate_structured_batch(
  owner: str,
  texts: List[dict],
  model_class: Type[BaseModel],
  schema_name: str,
  system_prompt: str,
  custom_metadata: Dict[str, Any] = {}
):
  jsonl_content = generate_structured_jsonl(
    texts=texts,
    system_prompt=system_prompt,
    model_class=model_class,
    schema_name=schema_name
  )

  with tempfile.NamedTemporaryFile(mode="w+", suffix=".jsonl", delete=False) as tmp:
    tmp.write(jsonl_content)
    tmp_path = tmp.name

  try:
    file_response = await create_batch_file(client, tmp_path)
    if not file_response:
      return None

    batch_response = await create_structured_batch_job(client, file_response.id)
    if not batch_response:
      return None

    with get_db_connection() as conn:
      insert_batch(
        conn=conn,
        batch_id=batch_response.id,
        file_input_id=file_response.id,
        owner=owner,
        data={
          "type": "structured_extraction",
          "schema": schema_name,
          "count": len(texts),
          **custom_metadata
        },
        type="structured",
        status=batch_response.status
      )

    return batch_response

  finally:
    if os.path.exists(tmp_path):
      os.remove(tmp_path)

async def orchestrate_embedding_batch(
  owner: str,
  texts: List[dict],
  custom_metadata: Dict[str, Any] = {}
):
  jsonl_content = generate_embedding_jsonl(texts=texts)

  with tempfile.NamedTemporaryFile(mode="w+", suffix=".jsonl", delete=False) as tmp:
    tmp.write(jsonl_content)
    tmp_path = tmp.name

  try:
    file_response = await create_batch_file(client, tmp_path)
    if not file_response:
      return None

    batch_response = await create_embedding_batch_job(client, file_response.id)
    if not batch_response:
      return None

    with get_db_connection() as conn:
      insert_batch(
        conn=conn,
        batch_id=batch_response.id,
        file_input_id=file_response.id,
        owner=owner,
        data={
          "type": "embeddings",
          "count": len(texts),
          **custom_metadata
        },
        type="embedding",
        status=batch_response.status
      )

    return batch_response

  finally:
    if os.path.exists(tmp_path):
      os.remove(tmp_path)

from openai import OpenAI

# --- Batch & File Operations ---
async def create_batch_file(client: OpenAI, file_path: str):
  try:
    return client.files.create(
      file=open(file_path, "rb"),
      purpose="batch"
    )
  except Exception as e:
    print(f"❌ Error creating batch file: {e}")
    return None

async def create_structured_batch_job(
  client: OpenAI, 
  input_file_id: str
):

  try:
    return client.batches.create(
      input_file_id=input_file_id,
      endpoint="/v1/responses",
      completion_window="24h"
    )
  except Exception as e:
    print(f"❌ Error creating structured batch job: {e}")
    return None

async def create_embedding_batch_job(
  client: OpenAI,
  input_file_id: str
):

  try:
    return client.batches.create(
      input_file_id=input_file_id,
      endpoint="/v1/embeddings",
      completion_window="24h"
    )
  except Exception as e:
    print(f"❌ Error creating embedding batch job: {e}")
    return None

async def retrieve_batch_status(client: OpenAI, batch_id: str):
  try:
    return client.batches.retrieve(batch_id)
  except Exception as e:
    print(f"❌ Error retrieving batch: {e}")
    return None

async def cancel_batch_job(client: OpenAI, batch_id: str):
  try:
    return client.batches.cancel(batch_id)
  except Exception as e:
    print(f"❌ Error cancelling batch: {e}")
    return None

async def list_batches(client: OpenAI, limit: int = 10):
  try:
    return client.batches.list(limit=limit)
  except Exception as e:
    print(f"❌ Error listing batches: {e}")
    return []

async def get_file_content(client: OpenAI, file_id: str):
  try:
    return client.files.content(file_id)
  except Exception as e:
    print(f"❌ Error retrieving file content: {e}")
    return None

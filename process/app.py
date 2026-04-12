import asyncio
from openai import OpenAI
from services.config import configs
from services.pg import get_db_connection
from services.orchestration import (
  run_data_extraction, 
  run_data_vectorization, 
  run_data_storage
)

async def main():
  client = OpenAI(api_key=configs.openai_api_key.get_secret_value())
  conn = get_db_connection()

  try:
    print("🚀 Starting Leaddits Data Pipeline...")

    # --- STAGE 1: Extract ---
    await run_data_extraction(conn, client)

    # --- STAGE 2: Vectorize ---
    #await run_data_vectorization(conn, client)

    # --- STAGE 3: Store ---
    #await run_data_storage(conn, client)

    print("✨ Pipeline execution complete.")

  except Exception as e:
    print(f"🔥 Critical Pipeline Failure: {e}")
  
  finally:
    conn.close()

if __name__ == "__main__":
  asyncio.run(main())

import asyncio
from services.config import configs
from services.pg import get_db_connection, deactivate_old_posts
from services.orchestration import (
  run_data_extraction, 
  run_data_vectorization
)

async def main():
  conn = get_db_connection()

  try:
    print("🚀 Starting Leaddits Real-time Pipeline...")

    # --- STAGE 0: Cleaning ---
    deactivate_old_posts(conn)

    # --- STAGE 1: Extract (LLM Parsing) ---
    await run_data_extraction(conn)

    # --- STAGE 2: Vectorize (Semantic Search) ---
    await run_data_vectorization(conn)

    print("✨ Pipeline execution complete. Data is now searchable.")

  except Exception as e:
    print(f"🔥 Critical Pipeline Failure: {e}")
  
  finally:
    if conn:
      conn.close()
      print("🔌 Database connection closed.")

if __name__ == "__main__":
  asyncio.run(main())


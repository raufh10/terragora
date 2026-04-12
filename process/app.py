import asyncio
from services.orchestration import run_data_extraction

if __name__ == "__main__":
  asyncio.run(run_data_extraction())


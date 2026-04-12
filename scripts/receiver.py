import asyncio
import os
import json
from nats.aio.client import Client as NATS
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()

async def run():
  # 1. Setup Config
  # Will now prioritize the value in your .env file
  nats_url = os.getenv("NATS_URL", "nats://127.0.0.1:4222")
  nc = NATS()

  try:
    # 2. Connect to NATS
    await nc.connect(nats_url)
    print(f"--- Connected to NATS at {nats_url} ---")
    print("Waiting for scraper events...")

    # 3. Define the message handler
    async def message_handler(msg):
      subject = msg.subject
      data = msg.data.decode()
      
      try:
        parsed_json = json.loads(data)
        formatted_data = json.dumps(parsed_json, indent=2)
      except json.JSONDecodeError:
        formatted_data = data

      print(f"\n[Received on {subject}]:")
      print(formatted_data)

    # 4. Subscribe to the subject
    await nc.subscribe("scraper.event", cb=message_handler)

    while True:
      await asyncio.sleep(1)

  except Exception as e:
    print(f"Error: {e}")
  finally:
    await nc.close()

if __name__ == '__main__':
  try:
    asyncio.run(run())
  except KeyboardInterrupt:
    print("\nStopping receiver...")


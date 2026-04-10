import os
import json
import asyncio

from nats.aio.client import Client as NATS

from dotenv import load_dotenv
# Load variables from .env
load_dotenv()

async def run():

  # 1. Setup Config
  nats_url = os.getenv("NATS_URL", "nats://127.0.0.1:4222")
  nc = NATS()

  # List of subjects to monitor
  subjects = [
    "scraper.event",
    "pipeline.event",
    "worker.status"
  ]

  try:
    # 2. Connect to NATS
    await nc.connect(nats_url, name="python-multi-subscriber")
    print(f"--- Connected to NATS at {nats_url} ---")

    # 3. Define the message handler
    async def message_handler(msg):
      subject = msg.subject
      data = msg.data.decode()

      try:
        parsed_json = json.loads(data)
        
        if isinstance(parsed_json, list):
          header = f"[Received BATCH of {len(parsed_json)} on {subject}]"
        else:
          header = f"[Received EVENT on {subject}]"
        
        formatted_data = json.dumps(parsed_json, indent=2)
      except json.JSONDecodeError:
        header = f"[Received RAW DATA on {subject}]"
        formatted_data = data

      print(f"\n{header}:")
      print(formatted_data)

    # 4. Subscribe to all defined subjects
    for sub in subjects:
      await nc.subscribe(sub, cb=message_handler)
      print(f"  -> Subscribed to: {sub}")

    print("\nWaiting for events... (Ctrl+C to stop)")

    while True:
      await asyncio.sleep(1)

  except Exception as e:
    print(f"Connection Error: {e}")
  finally:
    if nc.is_connected:
      await nc.close()
      print("NATS connection closed.")

if __name__ == '__main__':
  try:
    asyncio.run(run())
  except KeyboardInterrupt:
    print("\nStopping receiver...")

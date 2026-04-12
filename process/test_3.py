from openai import OpenAI
from dotenv import load_dotenv
import os
import sys
import json

# Load environment variables from .env
load_dotenv()

# Initialize client (it will read OPENAI_API_KEY automatically)
client = OpenAI()

# List batches
batches = client.batches.list(limit=10)

# Print results
for batch in batches.data:

    if not batch.id == "batch_69c5ea3ebca08190b28698ecd9f7027d":
      continue

    file_response = client.files.content(batch.error_file_id)
    content = file_response.text

    for line in content.splitlines():
      obj = json.loads(line)
      print(obj)

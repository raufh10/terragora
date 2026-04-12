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

    #if not batch.id == "batch_69c68c61c214819087613367276a7f2c":
      #continue

    print(batch)
    continue

    file_response = client.files.content(batch.output_file_id)
    content = file_response.text

    for line in content.splitlines():
      obj = json.loads(line)
      obj = obj.get("response").get("body").get("output")[0].get("content")[0].get("text")
      print(obj)

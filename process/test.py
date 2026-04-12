from openai import OpenAI
from dotenv import load_dotenv
import os
import json
from services.jsonl import extract_batch_embeddings, process_batch_output

load_dotenv()
client = OpenAI()

def run_extraction_test():
  embedding_batch_id = "batch_69bc3b75632881909032cc91b46a17ef"
  structured_batch_id = "batch_69c71bb3b33c81908a287e3a7976cf82"
  batches = client.batches.list(limit=20)

  for batch in batches.data:
    
    # --- HANDLE EMBEDDING BATCH ---
    if batch.id == embedding_batch_id:
      print(f"\n💎 Processing Embedding Batch: {batch.id}")
      if batch.output_file_id:
        file_response = client.files.content(batch.output_file_id)
        vectors = extract_batch_embeddings(file_response.text)
        print(f"✅ Successfully extracted {len(vectors)} vectors.")
        
        if vectors:
          for k, v in vectors.items():
            print(f"{k} - {v}")

      else:
        print(f"⚠️ Embedding batch status: {batch.status} (No output file yet)")

    # --- HANDLE STRUCTURED OUTPUT BATCH ---
    elif batch.id == structured_batch_id:
      print(f"\n📝 Processing Structured Output Batch: {batch.id}")
      if batch.output_file_id:
        file_response = client.files.content(batch.output_file_id)
        text_data = process_batch_output(file_response.text)
        print(f"✅ Successfully extracted {len(text_data)} text responses.")

        """        
        if text_data:
          for k, v in text_data.items():
            print(f"{k} - {v}")
        """

      else:
        print(f"⚠️ Structured batch status: {batch.status} (No output file yet)")

if __name__ == "__main__":
  run_extraction_test()


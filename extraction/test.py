import asyncio
import json
import os
import numpy as np
from typing import List, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def get_embedding(text: str) -> List[float]:
  try:
    response = client.embeddings.create(
      input=text,
      model="text-embedding-3-small"
    )
    return response.data[0].embedding
  except Exception:
    return [0.0] * 1536

def calculate_similarity(vector_a: List[float], vector_b: List[float]) -> float:
  if not vector_a or not vector_b: return 0.0
  a, b = np.array(vector_a), np.array(vector_b)
  norm_a, norm_b = np.linalg.norm(a), np.linalg.norm(b)
  if norm_a == 0 or norm_b == 0: return 0.0
  return float(np.dot(a, b) / (norm_a * norm_b))

def calculate_centroid(items: List[Dict[str, Any]], key_name: str, use_tfidf: bool = False) -> List[float]:
  if not items: return []
  embeddings = np.array([item["embedding"] for item in items])
  
  if not use_tfidf or len(items) < 2:
    return np.mean(embeddings, axis=0).tolist()
  
  texts = [item[key_name] for item in items]
  vectorizer = TfidfVectorizer()
  tfidf_matrix = vectorizer.fit_transform(texts)
  weights = np.asarray(tfidf_matrix.sum(axis=1)).flatten()
  weights = weights / weights.sum()
  return np.average(embeddings, axis=0, weights=weights).tolist()

async def process_data(use_tfidf: bool):
  with open('dummy_resume.json', 'r') as f:
    resume = json.load(f)
  with open('dummy_posts.json', 'r') as f:
    posts = json.load(f)

  for s in resume['skills']:
    s['embedding'] = await get_embedding(s['name'])
  for e in resume['experiences']:
    e['embedding'] = await get_embedding(e['description'])
  
  res_skill_centroid = calculate_centroid(resume['skills'], 'name', use_tfidf)

  results = []
  for post in posts:
    for s in post['skills']:
      s['embedding'] = await get_embedding(s['name'])
    for t in post['tasks']:
      t['embedding'] = await get_embedding(t['task'])
    
    post_task_centroid = calculate_centroid(post['tasks'], 'task', use_tfidf)
    score = calculate_similarity(res_skill_centroid, post_task_centroid)
    
    results.append({"role": post["role"], "score": round(score, 4)})

  return sorted(results, key=lambda x: x["score"], reverse=True)

async def main():
  print("--- Running Analysis: TF-IDF OFF ---")
  results_no_tfidf = await process_data(use_tfidf=False)
  print(json.dumps(results_no_tfidf, indent=2))

  print("\n--- Running Analysis: TF-IDF ON ---")
  results_tfidf = await process_data(use_tfidf=True)
  print(json.dumps(results_tfidf, indent=2))

if __name__ == "__main__":
  asyncio.run(main())


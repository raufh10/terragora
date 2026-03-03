import asyncio
from services.praw import AsyncPrawStarter
from services.extract import SubmissionsExtractor
from services.utils import DataManager
from services.db import get_supabase_client, insert_metadata, insert_vectors

async def run_pipeline(subreddit_config: dict):
  starter = AsyncPrawStarter()
  reddit = await starter.build()

  try:
    extractor = SubmissionsExtractor.from_config(reddit, subreddit_config)
    raw_posts = await extractor.collect()

    if not raw_posts:
      print(f"No posts found for r/{subreddit_config.get('subreddit')}")
      return

    print(f"Processing {len(raw_posts)} posts from r/{subreddit_config.get('subreddit')}...")
    
    # 1. AI Extraction & Embedding Generation
    enriched_output = await DataManager.merge_processed_data(raw_posts)
    enriched_posts = enriched_output["results"]

    metadata_payload = []
    vector_payload = []

    for item in enriched_posts:
      # 2. Extract embedding for the vector table
      embedding = item.pop("embedding", None)
      reddit_id = item.get("id")
      
      # 3. Rename 'id' to 'reddit_id' for Supabase conflict resolution
      item["reddit_id"] = item.pop("id")
      
      if embedding:
        vector_payload.append({"reddit_id": reddit_id, "embedding": embedding})
      
      metadata_payload.append(item)

    # 4. Sync to Database
    supabase = get_supabase_client()
    meta_success = await insert_metadata(supabase, metadata_payload)
    vec_success = await insert_vectors(vector_payload)

    if meta_success and vec_success:
      print(f"Successfully synced {len(metadata_payload)} items to database.")
    else:
      print(f"Sync status: Metadata={meta_success}, Vectors={vec_success}")

  finally:
    await reddit.close()

if __name__ == "__main__":
  search_config = {
    "subreddit": "lakers",
    "limit": 5,
    "sort": "new"
  }

  asyncio.run(run_pipeline(search_config))


from __future__ import annotations
from typing import List, Dict, Any
from process import process_submissions

class DataManager:
  @staticmethod
  async def merge_processed_data(collected_output: List[Dict[str, Any]]) -> Dict[str, Any]:
    extracted_results = await process_submissions(collected_output)
    
    extraction_map = {
      res["id"]: res["extracted_data"] 
      for res in extracted_results
    }

    final_data = []
    for post in collected_output:
      post_id = post.get("id")
      post["data"] = extraction_map.get(post_id)
      final_data.append(post)

    return {
      "count": len(final_data),
      "results": final_data
    }

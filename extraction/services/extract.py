from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class SubmissionsExtractor:
  reddit: Any
  subreddit: str
  limit: int = 10
  sort: str = "new"
  time_filter: str = "hour"
  fields: List[str] = field(default_factory=lambda: [
    "id", "title", "author", "link_flair_text", "score",
    "upvote_ratio", "num_comments", "created_utc",
    "is_self", "selftext", "url", "permalink"
  ])

  @classmethod
  def from_config(cls, reddit: Any, config: Dict[str, Any]) -> SubmissionsExtractor:
    return cls(
      reddit=reddit,
      subreddit=config.get("subreddit") or config.get("subreddit_name", ""),
      limit=int(config.get("limit", 10)),
      sort=(config.get("sort") or "new").lower(),
      time_filter=(config.get("time_filter") or "hour").lower(),
      fields=config.get("fields", cls.__dataclass_fields__["fields"].default_factory())
    )

  def _validate(self):
    if not self.subreddit:
      raise ValueError("subreddit is required")
    if self.sort not in {"hot", "new", "top", "rising"}:
      raise ValueError(f"Invalid sort: {self.sort}")
    if self.sort == "top" and self.time_filter not in {"hour", "day", "week", "month", "year", "all"}:
      raise ValueError(f"Invalid time_filter for top: {self.time_filter}")

  async def collect(self) -> List[Dict[str, Any]]:
    self._validate()
    data = []
    
    try:
      sr = await self.reddit.subreddit(self.subreddit, fetch=True)
      
      if self.sort == "top":
        iterator = sr.top(limit=self.limit, time_filter=self.time_filter)
      elif self.sort == "new":
        iterator = sr.new(limit=self.limit)
      elif self.sort == "rising":
        iterator = sr.rising(limit=self.limit)
      else:
        iterator = sr.hot(limit=self.limit)

      async for post in iterator:
        row = {}
        if "id" in self.fields: row["id"] = post.id
        if "title" in self.fields: row["title"] = post.title
        if "author" in self.fields: row["author"] = str(post.author) if post.author else None
        if "link_flair_text" in self.fields: row["link_flair_text"] = post.link_flair_text
        if "score" in self.fields: row["score"] = post.score
        if "upvote_ratio" in self.fields: row["upvote_ratio"] = post.upvote_ratio
        if "num_comments" in self.fields: row["num_comments"] = post.num_comments
        if "created_utc" in self.fields: row["created_utc"] = post.created_utc
        if "is_self" in self.fields: row["is_self"] = post.is_self
        if "selftext" in self.fields: row["selftext"] = post.selftext
        if "url" in self.fields: row["url"] = post.url
        if "permalink" in self.fields: row["permalink"] = f"https://reddit.com{post.permalink}"
        data.append(row)
        
    except Exception as e:
      # Return whatever was collected before the error occurred
      pass

    return data

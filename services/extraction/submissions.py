from typing import List, Dict, Any, Optional

class SubmissionsExtractor:
  def __init__(
    self,
    reddit,
    logger,
    subreddit: str,
    limit: int = 10,
    sort: str = "hot",
    time_filter: str = "day",
    fields: Optional[List[str]] = None,
  ):
    self.reddit = reddit
    self.logger = logger
    self.subreddit = subreddit
    self.limit = limit
    self.sort = sort
    self.time_filter = time_filter
    self.fields = fields or [
      "id", "title", "author", "score", "url",
      "num_comments", "created_utc", "selftext", "permalink"
    ]
    self.logger.debug(
      f"SubmissionsExtractor init | r/{self.subreddit} | limit={self.limit} "
      f"| sort={self.sort} | time={self.time_filter} | fields={self.fields}"
    )

  @classmethod
  def from_config(cls, reddit, logger, config: Dict[str, Any]) -> "SubmissionsExtractor":
    subreddit = config.get("subreddit") or config.get("subreddit_name")
    if not subreddit:
      raise ValueError("subreddit is required in config")
    limit = int(config.get("limit", 10))
    sort = (config.get("sort") or "hot").lower()
    time_filter = (config.get("time_filter") or "day").lower()
    fields = config.get("fields")
    return cls(
      reddit=reddit,
      logger=logger,
      subreddit=subreddit,
      limit=limit,
      sort=sort,
      time_filter=time_filter,
      fields=fields,
    )

  def _validate(self):
    if not self.subreddit:
      raise ValueError("subreddit is required")
    if self.sort not in {"hot", "new", "top", "rising"}:
      raise ValueError("sort must be one of {'hot','new','top','rising'}")
    if self.sort == "top" and self.time_filter not in {"hour", "day", "week", "month", "year", "all"}:
      raise ValueError("time_filter must be one of {'hour','day','week','month','year','all'}")

  async def collect(self) -> List[Dict[str, Any]]:

    self._validate()
    data: List[Dict[str, Any]] = []
    self.logger.info(f"Collecting submissions from r/{self.subreddit}")

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
        row: Dict[str, Any] = {}
        if "id" in self.fields: row["id"] = post.id
        if "title" in self.fields: row["title"] = post.title
        if "author" in self.fields: row["author"] = str(post.author) if post.author is not None else None
        if "score" in self.fields: row["score"] = post.score
        if "url" in self.fields: row["url"] = post.url
        if "num_comments" in self.fields: row["num_comments"] = post.num_comments
        if "created_utc" in self.fields: row["created_utc"] = post.created_utc
        if "selftext" in self.fields: row["selftext"] = post.selftext
        if "permalink" in self.fields: row["permalink"] = f"https://reddit.com{post.permalink}"
        data.append(row)

      self.logger.info(f"Collected {len(data)} submissions from r/{self.subreddit}")

    except Exception as e:
      self.logger.exception(f"Failed collecting submissions: {e}")

    return data

  def __repr__(self):
    return (
      f"SubmissionsExtractor(subreddit={self.subreddit}, "
      f"limit={self.limit}, sort={self.sort}, time_filter={self.time_filter}, "
      f"fields={self.fields})"
    )

# Sync Praw Not Used
"""
class SubmissionsExtractor:
  def __init__(
    self,
    reddit,
    logger,
    subreddit: str,
    limit: int = 10,
    sort: str = "hot",
    time_filter: str = "day",
    fields: Optional[List[str]] = None,
  ):
    self.reddit = reddit
    self.logger = logger
    self.subreddit = subreddit
    self.limit = limit
    self.sort = sort
    self.time_filter = time_filter
    self.fields = fields or [
      "id", "title", "author", "score", "url",
      "num_comments", "created_utc", "selftext", "permalink"
    ]
    self.logger.debug(
      f"SubmissionsExtractor init | r/{self.subreddit} | limit={self.limit} "
      f"| sort={self.sort} | time={self.time_filter} | fields={self.fields}"
    )

  @classmethod
  def from_config(cls, reddit, logger, config: Dict[str, Any]) -> "SubmissionsExtractor":
    subreddit = config.get("subreddit") or config.get("subreddit_name")
    if not subreddit:
      raise ValueError("subreddit is required in config")
    limit = int(config.get("limit", 10))
    sort = (config.get("sort") or "hot").lower()
    time_filter = (config.get("time_filter") or "day").lower()
    fields = config.get("fields")
    return cls(
      reddit=reddit,
      logger=logger,
      subreddit=subreddit,
      limit=limit,
      sort=sort,
      time_filter=time_filter,
      fields=fields,
    )

  def _validate(self):
    if not self.subreddit:
      raise ValueError("subreddit is required")
    if self.sort not in {"hot", "new", "top", "rising"}:
      raise ValueError("sort must be one of {'hot','new','top','rising'}")
    if self.sort == "top" and self.time_filter not in {"hour", "day", "week", "month", "year", "all"}:
      raise ValueError("time_filter must be one of {'hour','day','week','month','year','all'}")

  def collect(self) -> List[Dict[str, Any]]:
    self._validate()
    data: List[Dict[str, Any]] = []
    self.logger.info(f"Collecting submissions from r/{self.subreddit}")
    try:
      sr = self.reddit.subreddit(self.subreddit)
      if self.sort == "top":
        iterator = sr.top(limit=self.limit, time_filter=self.time_filter)
      elif self.sort == "new":
        iterator = sr.new(limit=self.limit)
      elif self.sort == "rising":
        iterator = sr.rising(limit=self.limit)
      else:
        iterator = sr.hot(limit=self.limit)

      for post in iterator:
        row = {}
        if "id" in self.fields: row["id"] = post.id
        if "title" in self.fields: row["title"] = post.title
        if "author" in self.fields: row["author"] = str(post.author)
        if "score" in self.fields: row["score"] = post.score
        if "url" in self.fields: row["url"] = post.url
        if "num_comments" in self.fields: row["num_comments"] = post.num_comments
        if "created_utc" in self.fields: row["created_utc"] = post.created_utc
        if "selftext" in self.fields: row["selftext"] = post.selftext
        if "permalink" in self.fields: row["permalink"] = f"https://reddit.com{post.permalink}"
        data.append(row)

      self.logger.info(f"Collected {len(data)} submissions from r/{self.subreddit}")
    except Exception as e:
      self.logger.exception(f"Failed collecting submissions: {e}")
    return data

  def __repr__(self):
    return (
      f"SubmissionsExtractor(subreddit={self.subreddit}, "
      f"limit={self.limit}, sort={self.sort}, time_filter={self.time_filter}, "
      f"fields={self.fields})"
    )
"""

from typing import List, Dict, Any, Optional

class RulesExtractor:

  def __init__(
    self,
    reddit,
    logger,
    subreddit: str,
    fields: Optional[List[str]] = None,
  ):
    self.reddit = reddit
    self.logger = logger
    self.subreddit = subreddit
    self.fields = fields or [
      "short_name",
      "description",
      "kind",
      "violation_reason",
      "created_utc",
      "priority",
    ]
    self.logger.debug(
      f"RulesExtractor init | r/{self.subreddit} | fields={self.fields}"
    )

  @classmethod
  def from_config(cls, reddit, logger, config: Dict[str, Any]) -> "RulesExtractor":
    subreddit = config.get("subreddit") or config.get("subreddit_name")
    if not subreddit:
      raise ValueError("subreddit is required in config")
    fields = config.get("fields")
    return cls(
      reddit=reddit,
      logger=logger,
      subreddit=subreddit,
      fields=fields,
    )

  def _validate(self):
    if not self.subreddit:
      raise ValueError("subreddit is required")

  async def collect(self) -> List[Dict[str, Any]]:

    self._validate()
    data: List[Dict[str, Any]] = []
    self.logger.info(f"Collecting rules from r/{self.subreddit}")

    try:
      sr = await self.reddit.subreddit(self.subreddit, fetch=True)

      rules_list = []
      try:
        rules_list = await sr.rules()
      except TypeError:
        try:
          async for rule in sr.rules:
            rules_list.append(rule)
        except TypeError:
          get_rules = getattr(sr.rules, "get_rules", None)
          if callable(get_rules):
            rules_list = await get_rules()
          else:
            self.logger.warning("Could not resolve rules via known asyncpraw patterns")

      for rule in (rules_list.get("rules") or []):
        row: Dict[str, Any] = {}
        for f in self.fields:
          row[f] = rule.get(f)
        if not row.get("short_name"):
          row["short_name"] = rule.get("violation_reason") or "(unnamed rule)"
        if any(v is not None for v in row.values()):
          data.append(row)

      self.logger.info(f"Collected {len(data)} rule(s) from r/{self.subreddit}")

    except Exception as e:
      self.logger.exception(f"Failed collecting rules: {e}")

    return data

  def __repr__(self):
    return (
      f"RulesExtractor(subreddit={self.subreddit}, "
      f"fields={self.fields})"
    )

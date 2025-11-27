import os
import json
import yaml
import asyncio
import requests
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple, Optional

from services.database import db, agendas, submissions
from logger import start_logger

PROMPTS_PATH = "data/prompts.yaml"
logger = start_logger()


class AgendaProcessor:
  def __init__(self):
    from services.config import settings
    self.supabase = db.get_supabase_client()
    self.api = settings.API_ENDPOINT.rstrip("/")

    self.fetch_url = f"{self.api}/submissions/fetch"
    self.run_url = f"{self.api}/analysis/run"

    self.system_prompt, self.user_prompt_tpl = self._load_yaml(PROMPTS_PATH)

  @staticmethod
  def _load_yaml(path: str) -> Tuple[str, str]:
    with open(path, "r", encoding="utf-8") as f:
      data = yaml.safe_load(f)

    block = data.get("discover_category")
    if not isinstance(block, dict):
      raise ValueError("Missing required key 'discover_category' in YAML")

    system_prompt = block.get("system_prompt")
    user_prompt = block.get("user_prompt")

    if not system_prompt or not user_prompt:
      raise ValueError("YAML missing system_prompt or user_prompt")

    return system_prompt.strip(), user_prompt.strip()

  @classmethod
  def run(cls):
    processor = cls()
    processor._run_all()

  def _run_all(self):
    try:
      agenda_list = asyncio.run(agendas.select(self.supabase, logger)) or []
    except Exception as e:
      logger.error(f"Agenda select failed: {e}")
      return

    if not agenda_list:
      logger.warning("No agendas found")
      return

    logger.info(f"Processing {len(agenda_list)} agendas")

    for idx, agenda_row in enumerate(agenda_list, start=1):
      logger.info(f"▶ Agenda {idx}/{len(agenda_list)} | id={agenda_row.get('id')}")
      self._process_single_agenda(agenda_row)

  def _process_single_agenda(self, agenda: Dict[str, Any]):
    agenda_id = agenda.get("id")
    subreddit = agenda.get("subreddit")

    if not subreddit:
      logger.error("Missing subreddit; skipping")
      return

    fetch_payload = {"subreddit": subreddit}
    insert_buffer = []

    try:
      resp = requests.post(self.fetch_url, json=fetch_payload, timeout=60)
      if not resp.ok:
        logger.error(f"Fetch failed [{resp.status_code}] {resp.text[:200]}")
        return

      body = resp.json()
      posts = body.get("results", {}).get(subreddit)

      if not posts:
        logger.warning(f"No posts returned for r/{subreddit}")
        return

      try:
        existing = asyncio.run(submissions.select_reddit_ids(self.supabase, logger, subreddit)) or []
      except Exception:
        existing = []

      existing = set(existing)

      for post in posts:
        rid = post.get("id")
        if not rid:
          continue

        new_post = dict(post)
        new_post.pop("id", None)

        insert_buffer.append({
          "reddit_id": rid,
          "subreddit": subreddit,
          "data": new_post
        })

    except Exception as e:
      logger.error(f"Fetch exception: {e}")

    if insert_buffer:
      try:
        result = asyncio.run(submissions.insert(self.supabase, logger, insert_buffer))
        logger.info(f"Inserted {len(insert_buffer)} posts" if result else "Insert failed")
      except Exception as e:
        logger.error(f"Insert exception: {e}")

    self._label_unprocessed(subreddit)

  def _label_unprocessed(self, subreddit: str):
    try:
      posts = asyncio.run(submissions.select_to_label(self.supabase, logger, subreddit)) or []
    except Exception as e:
      logger.error(f"Select_to_label failed: {e}")
      return

    posts = posts[:25]
    payloads = []

    for item in posts:
      pdata = item.get("data") or {}
      user_prompt = self.user_prompt_tpl.format(
        subreddit=subreddit,
        link_flair_text=pdata.get("link_flair_text") or "",
        title=pdata.get("title") or "-",
        selftext=pdata.get("selftext") or "",
      )

      payloads.append({
        "submission_id": item.get("id"),
        "system_prompt": self.system_prompt,
        "user_prompt": user_prompt
      })

    results = []

    for p in payloads:
      sid = p["submission_id"]
      if not sid: 
        continue

      try:
        resp = requests.post(self.run_url, json={
          "system_prompt": p["system_prompt"],
          "user_prompt": p["user_prompt"]
        }, timeout=60)

        if not resp.ok:
          continue

        parsed = resp.json()

        results.append({
          "submission_id": sid,
          "to_insert": {
            "category": parsed["category"],
            "category_data": parsed["category_data"]["subcategories"]
          }
        })

      except Exception as e:
        logger.error(f"Run prompt failed for {sid}: {e}")

    if results:
      try:
        asyncio.run(submissions.update_category_data(self.supabase, logger, results))
        logger.info("Category updates complete")
      except Exception as e:
        logger.error(f"Update exception: {e}")

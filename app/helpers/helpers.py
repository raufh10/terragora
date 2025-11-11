from fastapi.templating import Jinja2Templates
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import itertools
import os
import re

# Templates (resolve ../templates from helpers/)
HELPERS_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.dirname(HELPERS_DIR)
templates = Jinja2Templates(directory=os.path.join(APP_DIR, "templates"))

# Demo stores / config
USERS: Dict[str, str] = {}
CURRENT_EMAIL: Optional[str] = "demo@example.com"

TYPE_OPTIONS = ["jobs", "services", "discussion", "announcement"]
LOCATION_OPTIONS = ["global", "US", "EU", "APAC", "Remote"]

AGENDA = {
  "agenda_name": "My Daily Feed",
  "subreddit": "lakers",
  "data": {"type": "discussion", "location": "global"},
}

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Dashboard mock data
_post_ids = itertools.count(1)

def _mk_item(title, subreddit, author, score, minutes_ago, selftext="", preview_url="", permalink="") -> Dict:
  dt = datetime.utcnow() - timedelta(minutes=minutes_ago)
  return {
    "id": next(_post_ids),
    "title": title,
    "subreddit": subreddit,
    "author": author,
    "score": score,
    "created_utc": int(dt.timestamp()),
    "created_human": dt.strftime("%Y-%m-%d %H:%M UTC"),
    "selftext": selftext,
    "preview_url": preview_url,
    "reddit_url": f"https://reddit.com{permalink or f'/r/{subreddit}/comments/abcdef/mock'}",
  }

MOCK_ITEMS: List[Dict] = [
  _mk_item("Trade Rumor: Big move incoming?", "lakers", "hoopsfan42", 523, 20, "What do you think about this rumor?"),
  _mk_item("New build advice: 7800X3D vs 9900K", "buildapc", "techie", 199, 60, preview_url="https://placehold.co/600x300"),
] * 4

PAGE_SIZE = 6

def render_auth_partial(request, partial_name: str, context: Optional[Dict] = None):
  print(f"[ROUTE] Rendering auth partial: {partial_name}")
  ctx = {"request": request}
  if context:
    ctx.update(context)
  return templates.TemplateResponse(f"partials/{partial_name}.html", ctx)

def paginate(items: List[Dict], page: int) -> Tuple[List[Dict], bool, int]:
  start = (page - 1) * PAGE_SIZE
  return items[start:start+PAGE_SIZE], (start+PAGE_SIZE) < len(items), page + 1

def filter_and_sort(items, q, subreddit, sort, time_filter):
  # simplified unchanged behavior for now
  return items

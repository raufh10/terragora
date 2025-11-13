from datetime import datetime, timedelta

# ---------------------------------------
# MOCK PROFILE & AGENDA
# ---------------------------------------

MOCK_PROFILE = {
  "name": "John Doe",
  "email": "demo@example.com"
}

MOCK_AGENDA = {
  "agenda_name": "My Daily Feed",
  "subreddit": "lakers",
  "data": {
    "type": "discussion",
    "location": "global"
  },
}

TYPE_OPTIONS = ["jobs", "services", "discussion", "announcement"]
LOCATION_OPTIONS = ["global", "US", "EU", "APAC", "Remote"]

# ---------------------------------------
# FEED MOCK DATA
# ---------------------------------------

PAGE_SIZE = 6

def _mk_item(
  idx: int,
  title: str,
  minutes_ago: int,
  preview_url: str = "",
  category: str = "",
  tags=None
):
  dt = datetime.utcnow() - timedelta(minutes=minutes_ago)

  return {
    "id": idx,
    "title": title,
    "preview_url": preview_url,
    "created_human": dt.strftime("%Y-%m-%d %H:%M UTC"),
    "category": category or "uncategorized",
    "tags": tags or [],
    "reddit_url": f"https://reddit.com/r/example/comments/mock_{idx}",
  }


def _mock_items():
  return [
    _mk_item(1, "Trade Rumor: Big move incoming?", 20, "", "discussion", ["lakers", "rumor"]),
    _mk_item(2, "New build advice: 7800X3D vs 9900K", 60, "https://placehold.co/600x300", "services", ["buildapc", "hardware"]),
    _mk_item(3, "AEW show tonight: predictions?", 90, "", "discussion", ["aew", "wrestling"]),
    _mk_item(4, "Ask HN: Best lightweight job tracker?", 120, "", "jobs", ["hackernews", "tools"]),
    _mk_item(5, "City guide: food near arena?", 180, "", "discussion", ["losangeles", "food"]),
    _mk_item(6, "Hot take: top shot selection", 240, "", "announcement", ["lakers", "opinion"]),
    _mk_item(7, "PSA: Hiring data analysts (remote)", 300, "", "jobs", ["forhire", "remote"]),
    _mk_item(8, "Show & Tell: My CLI Reddit client", 360, "https://placehold.co/500x200", "services", ["python", "cli"]),
    _mk_item(9, "Match thread: Game night chat", 420, "", "discussion", ["lakers", "gamethread"]),
    _mk_item(10, "New Mod Tool preview", 500, "", "announcement", ["modsupport", "preview"]),
  ]

# ---------------------------------------
# MOCK AUTH STORE
# ---------------------------------------

MOCK_USERS = {
  "demo@example.com": "password123"
}

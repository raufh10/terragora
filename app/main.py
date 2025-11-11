from fastapi import FastAPI, Request, Form, Query, status
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import itertools
import os
import re

app = FastAPI(title="FastAPI + Jinja2 + HTMX + Alpine")

# --------------------------
# Static & Templates
# --------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
app.mount("/static", StaticFiles(directory=os.path.join(ROOT_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# --------------------------
# Demo stores / config
# --------------------------

# Auth (demo only)
USERS: Dict[str, str] = {}  # email -> password (plain text for demo only)
CURRENT_EMAIL: Optional[str] = "demo@example.com"  # pretend logged in

# Settings (Agenda)
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

def _mk_item(
  title: str,
  subreddit: str,
  author: str,
  score: int,
  minutes_ago: int,
  selftext: str = "",
  preview_url: str = "",
  permalink: str = ""
) -> Dict:
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
  _mk_item("AEW show tonight: predictions?", "AEWOfficial", "wrestlebot", 88, 90),
  _mk_item("Ask HN: Best lightweight job tracker?", "hackernews", "shipit", 151, 120),
  _mk_item("City guide: food near arena?", "losangeles", "eatlocal", 44, 180, "Looking for recommendations!"),
  _mk_item("Hot take: top shot selection", "lakers", "x_o_coach", 310, 240),
  _mk_item("PSA: Hiring data analysts (remote)", "forhire", "hr_wiz", 401, 300),
  _mk_item("Show & Tell: My CLI Reddit client", "python", "dev_monk", 265, 360, preview_url="https://placehold.co/500x200"),
  _mk_item("Match thread: Game night chat", "lakers", "modteam", 712, 420),
  _mk_item("New Mod Tool preview", "ModSupport", "admin", 66, 500, "We’re rolling out a new feature soon."),
] * 2  # duplicate for longer pagination

PAGE_SIZE = 6

# --------------------------
# Helpers (render / paginate / filter)
# --------------------------

def render_auth_partial(request: Request, partial_name: str, context: Optional[Dict] = None) -> HTMLResponse:
  print(f"[PARTIAL] render_auth_partial -> partials/{partial_name}.html", flush=True)
  ctx = {"request": request}
  if context:
    ctx.update(context)
  return templates.TemplateResponse(f"partials/{partial_name}.html", ctx)

def render_settings_partial(request: Request, partial_name: str, context: Optional[Dict] = None) -> HTMLResponse:
  print(f"[PARTIAL] render_settings_partial -> partials/{partial_name}.html", flush=True)
  ctx = {
    "request": request,
    "current_email": CURRENT_EMAIL,
    "agenda": AGENDA,
    "type_options": TYPE_OPTIONS,
    "location_options": LOCATION_OPTIONS,
  }
  if context:
    ctx.update(context)
  return templates.TemplateResponse(f"partials/{partial_name}.html", ctx)

def paginate(items: List[Dict], page: int) -> Tuple[List[Dict], bool, int]:
  start = (page - 1) * PAGE_SIZE
  end = start + PAGE_SIZE
  chunk = items[start:end]
  has_more = end < len(items)
  next_page = page + 1
  return chunk, has_more, next_page

def filter_and_sort(
  items: List[Dict],
  q: Optional[str],
  subreddit: Optional[str],
  sort: Optional[str],
  time_filter: Optional[str]
) -> List[Dict]:
  data = items

  # q filter
  if q:
    qlow = q.lower()
    data = [
      it for it in data
      if qlow in it["title"].lower()
      or qlow in it.get("author","").lower()
      or qlow in it.get("subreddit","").lower()
      or qlow in it.get("selftext","").lower()
    ]

  # subreddit filter
  if subreddit:
    s = subreddit.lower().strip()
    data = [it for it in data if it["subreddit"].lower() == s]

  # time_filter (simple mock)
  now = datetime.utcnow().timestamp()
  if time_filter == "day":
    cutoff = now - 24*3600
    data = [it for it in data if it["created_utc"] >= cutoff]
  elif time_filter == "week":
    cutoff = now - 7*24*3600
    data = [it for it in data if it["created_utc"] >= cutoff]
  elif time_filter == "month":
    cutoff = now - 30*24*3600
    data = [it for it in data if it["created_utc"] >= cutoff]
  # year/all: skip in mock

  # sort mock
  sort = (sort or "hot").lower()
  if sort == "new":
    data = sorted(data, key=lambda it: it["created_utc"], reverse=True)
  elif sort == "top":
    data = sorted(data, key=lambda it: it["score"], reverse=True)
  elif sort == "rising":
    def rising_score(it):
      age = max(1, int(now - it["created_utc"]))
      return it["score"] / age
    data = sorted(data, key=rising_score, reverse=True)
  else:  # hot (mock): score weighted by recency
    def hot_score(it):
      age = max(1, int(now - it["created_utc"]))
      return it["score"] / (age ** 0.6)
    data = sorted(data, key=hot_score, reverse=True)

  return data

# --------------------------
# Pages
# --------------------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
  print("[ROUTE] GET / -> index.html", flush=True)
  return templates.TemplateResponse("index.html", {"request": request})

@app.get("/account", response_class=HTMLResponse)
async def account_page(request: Request):
  print("[ROUTE] GET /account -> account.html", flush=True)
  return templates.TemplateResponse("account.html", {"request": request})

@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
  print("[ROUTE] GET /settings -> settings.html", flush=True)
  return templates.TemplateResponse(
    "settings.html",
    {
      "request": request,
      "current_email": CURRENT_EMAIL,
      "agenda": AGENDA,
      "type_options": TYPE_OPTIONS,
      "location_options": LOCATION_OPTIONS,
    }
  )

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
  request: Request,
  q: Optional[str] = Query(None),
  sort: Optional[str] = Query("hot"),
  time_filter: Optional[str] = Query("day"),
  subreddit: Optional[str] = Query(None),
  page: int = Query(1)
):
  print(f"[ROUTE] GET /dashboard -> q={q} sort={sort} time_filter={time_filter} subreddit={subreddit} page={page}", flush=True)
  filtered = filter_and_sort(MOCK_ITEMS, q, subreddit, sort, time_filter)
  items, has_more, next_page = paginate(filtered, page)

  return templates.TemplateResponse(
    "dashboard.html",
    {
      "request": request,
      "items": items,
      "has_more": has_more,
      "next_page": next_page,
      "q": q, "sort": sort, "time_filter": time_filter, "subreddit": subreddit,
    }
  )

# --------------------------
# HTMX fragments
# --------------------------
@app.get("/dashboard/feed", response_class=HTMLResponse)
async def feed_fragment(
  request: Request,
  q: Optional[str] = Query(None),
  sort: Optional[str] = Query("hot"),
  time_filter: Optional[str] = Query("day"),
  subreddit: Optional[str] = Query(None),
  page: int = Query(1)
):
  print(f"[FRAGMENT] GET /dashboard/feed -> q={q} sort={sort} time_filter={time_filter} subreddit={subreddit} page={page}", flush=True)
  filtered = filter_and_sort(MOCK_ITEMS, q, subreddit, sort, time_filter)
  items, has_more, next_page = paginate(filtered, page)

  return templates.TemplateResponse(
    "partials/feed.html",
    {
      "request": request,
      "items": items,
      "has_more": has_more,
      "next_page": next_page,
      "q": q, "sort": sort, "time_filter": time_filter, "subreddit": subreddit,
    }
  )

# --------------------------
# Auth partials
# --------------------------
@app.get("/auth/partials/sign-up", response_class=HTMLResponse)
async def partial_sign_up(request: Request):
  print("[PARTIAL] GET /auth/partials/sign-up", flush=True)
  return render_auth_partial(request, "sign_up")

@app.get("/auth/partials/login", response_class=HTMLResponse)
async def partial_login(request: Request):
  print("[PARTIAL] GET /auth/partials/login", flush=True)
  return render_auth_partial(request, "login")

@app.get("/auth/partials/forgot", response_class=HTMLResponse)
async def partial_forgot(request: Request):
  print("[PARTIAL] GET /auth/partials/forgot", flush=True)
  return render_auth_partial(request, "forget_password")

# --------------------------
# Settings partials & handlers
# --------------------------
@app.get("/settings/partials/account", response_class=HTMLResponse)
async def partial_account_settings(request: Request):
  print("[PARTIAL] GET /settings/partials/account", flush=True)
  return render_settings_partial(request, "account_settings")

@app.get("/settings/partials/agenda", response_class=HTMLResponse)
async def partial_agenda_settings(request: Request):
  print("[PARTIAL] GET /settings/partials/agenda", flush=True)
  return render_settings_partial(request, "agenda_settings")

@app.post("/settings/account/change-email", response_class=HTMLResponse)
async def settings_change_email(
  request: Request,
  current_email: Optional[str] = Form(None),
  new_email: str = Form(...)
):
  print(f"[ACTION] POST /settings/account/change-email -> new_email={new_email}", flush=True)
  global CURRENT_EMAIL
  new_email = new_email.strip().lower()
  if not EMAIL_RE.match(new_email):
    return render_settings_partial(request, "account_settings", {"error": "Please enter a valid email address."})
  if CURRENT_EMAIL and new_email == CURRENT_EMAIL:
    return render_settings_partial(request, "account_settings", {"error": "New email is the same as current."})

  CURRENT_EMAIL = new_email
  return render_settings_partial(request, "account_settings", {"success": "Email updated."})

@app.post("/settings/account/change-password", response_class=HTMLResponse)
async def settings_change_password(
  request: Request,
  old_password: str = Form(...),
  new_password: str = Form(...),
  confirm_password: str = Form(...)
):
  print("[ACTION] POST /settings/account/change-password (passwords hidden)", flush=True)
  if len(new_password) < 8:
    return render_settings_partial(request, "account_settings", {"error": "New password must be at least 8 characters."})
  if new_password != confirm_password:
    return render_settings_partial(request, "account_settings", {"error": "Passwords do not match."})
  return render_settings_partial(request, "account_settings", {"success": "Password updated."})

@app.post("/settings/account/delete", response_class=HTMLResponse)
async def settings_delete_account(request: Request, confirm: Optional[str] = Form(None)):
  print(f"[ACTION] POST /settings/account/delete -> confirm={'SET' if confirm else 'EMPTY'}", flush=True)
  if confirm != "DELETE":
    return render_settings_partial(request, "account_settings", {"error": "Type DELETE to confirm account deletion."})
  global CURRENT_EMAIL, USERS, TODOS, AGENDA
  USERS = {}
  CURRENT_EMAIL = None
  TODOS = []  # nuke todos for demo effect
  AGENDA = {
    "agenda_name": "My Daily Feed",
    "subreddit": "lakers",
    "data": {"type": "discussion", "location": "global"},
  }
  return render_settings_partial(request, "account_settings", {"success": "Account deleted (demo)."})

@app.post("/settings/agenda/update", response_class=HTMLResponse)
async def settings_agenda_update(
  request: Request,
  agenda_name: str = Form(...),
  subreddit: str = Form(...),
  data_type: str = Form(...),
  data_location: str = Form(...)
):
  print(f"[ACTION] POST /settings/agenda/update -> name={agenda_name} subreddit={subreddit} type={data_type} location={data_location}", flush=True)
  global AGENDA
  agenda_name = agenda_name.strip()
  subreddit = subreddit.strip()
  if not agenda_name:
    return render_settings_partial(request, "agenda_settings", {"error": "Agenda name is required."})
  if not subreddit:
    return render_settings_partial(request, "agenda_settings", {"error": "Subreddit is required."})
  if data_type not in TYPE_OPTIONS:
    return render_settings_partial(request, "agenda_settings", {"error": "Invalid type selected."})
  if data_location not in LOCATION_OPTIONS:
    return render_settings_partial(request, "agenda_settings", {"error": "Invalid location selected."})

  AGENDA = {
    "agenda_name": agenda_name,
    "subreddit": subreddit,
    "data": {"type": data_type, "location": data_location},
  }
  return render_settings_partial(request, "agenda_settings", {"success": "Agenda updated."})

# --------------------------
# AI action (mock)
# --------------------------
@app.post("/ai/reply", response_class=HTMLResponse)
async def ai_reply(id: str = Form(...)):
  print(f"[ACTION] POST /ai/reply -> id={id}", flush=True)
  # mock response only
  return HTMLResponse(f"""
  <div class="card mt">
    <strong>AI Draft for post #{id}:</strong>
    <p class="muted">Hey! Here’s a quick thought — this looks promising. What’s your timeline and budget?</p>
  </div>
  """)

# --------------------------
# Healthcheck
# --------------------------
@app.get("/healthz")
async def healthz():
  print("[ROUTE] GET /healthz", flush=True)
  return PlainTextResponse("ok")

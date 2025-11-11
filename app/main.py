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

# --------------------------
# Dashboard mock data
# --------------------------
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

# --------------------------
# Helpers
# --------------------------
def render_auth_partial(request: Request, partial_name: str, context: Optional[Dict] = None) -> HTMLResponse:
  print(f"[ROUTE] Rendering auth partial: {partial_name}")
  ctx = {"request": request}
  if context:
    ctx.update(context)
  return templates.TemplateResponse(f"partials/{partial_name}.html", ctx)

def paginate(items: List[Dict], page: int):
  start = (page - 1) * PAGE_SIZE
  return items[start:start+PAGE_SIZE], (start+PAGE_SIZE) < len(items), page + 1

def filter_and_sort(items, q, subreddit, sort, time_filter):
  return items  # simplified unchanged behavior for now

# --------------------------
# Pages
# --------------------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
  print("[ROUTE] GET /")
  return templates.TemplateResponse("index.html", {"request": request})

@app.get("/account", response_class=HTMLResponse)
async def account_page(request: Request):
  print("[ROUTE] GET /account")
  return templates.TemplateResponse("account.html", {"request": request})

@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
  print("[ROUTE] GET /settings")
  return templates.TemplateResponse(
    "settings.html",
    {"request": request, "current_email": CURRENT_EMAIL, "agenda": AGENDA}
  )

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, page: int = Query(1)):
  print(f"[ROUTE] GET /dashboard page={page}")
  items, has_more, next_page = paginate(MOCK_ITEMS, page)
  return templates.TemplateResponse(
    "dashboard.html",
    {"request": request, "items": items, "has_more": has_more, "next_page": next_page}
  )

# --------------------------
# HTMX Feed Fragment
# --------------------------
@app.get("/dashboard/feed", response_class=HTMLResponse)
async def feed_fragment(request: Request, page: int = Query(1)):
  print(f"[ROUTE] GET /dashboard/feed page={page}")
  items, has_more, next_page = paginate(MOCK_ITEMS, page)
  return templates.TemplateResponse(
    "partials/feed.html",
    {"request": request, "items": items, "has_more": has_more, "next_page": next_page}
  )

# --------------------------
# Auth Partials
# --------------------------
@app.get("/auth/partials/sign-up", response_class=HTMLResponse)
async def partial_sign_up(request: Request):
  print("[ROUTE] GET /auth/partials/sign-up")
  return render_auth_partial(request, "sign_up")

@app.get("/auth/partials/login", response_class=HTMLResponse)
async def partial_login(request: Request):
  print("[ROUTE] GET /auth/partials/login")
  return render_auth_partial(request, "login")

@app.get("/auth/partials/forgot", response_class=HTMLResponse)
async def partial_forgot(request: Request):
  print("[ROUTE] GET /auth/partials/forget_password")
  return render_auth_partial(request, "forget_password")

# --------------------------
# Healthcheck
# --------------------------
@app.get("/healthz")
async def healthz():
  print("[ROUTE] GET /healthz")
  return PlainTextResponse("ok")

from fastapi import FastAPI, Request, Form, status
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List, Dict, Optional
import itertools
import os
import re

app = FastAPI(title="FastAPI + Jinja2 + HTMX + Alpine")

# --- static and templates ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
app.mount("/static", StaticFiles(directory=os.path.join(ROOT_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# --- demo data stores ---
_id_counter = itertools.count(1)
TODOS: List[Dict] = [
  {"id": next(_id_counter), "title": "Ship MVP", "done": False},
  {"id": next(_id_counter), "title": "Write docs", "done": True},
]

# Auth demo store
USERS: Dict[str, str] = {}  # email -> password (plain text for demo only)
CURRENT_EMAIL: Optional[str] = "demo@example.com"  # pretend the user is logged in as this

# Agenda demo store
TYPE_OPTIONS = ["jobs", "services", "discussion", "announcement"]
LOCATION_OPTIONS = ["global", "US", "EU", "APAC", "Remote"]
AGENDA = {
  "agenda_name": "My Daily Feed",
  "subreddit": "lakers",
  "data": {"type": "discussion", "location": "global"},
}

# --- utilities ---
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def render_items_fragment(request: Request) -> HTMLResponse:
  return templates.TemplateResponse(
    "partials/todo_items.html",
    {"request": request, "todos": TODOS}
  )

def render_auth_partial(request: Request, partial_name: str, context: Optional[Dict] = None) -> HTMLResponse:
  ctx = {"request": request}
  if context:
    ctx.update(context)
  return templates.TemplateResponse(f"partials/{partial_name}.html", ctx)

def render_settings_partial(request: Request, partial_name: str, context: Optional[Dict] = None) -> HTMLResponse:
  ctx = {"request": request}
  # Provide common context for settings screens
  ctx.update({
    "current_email": CURRENT_EMAIL,
    "agenda": AGENDA,
    "type_options": TYPE_OPTIONS,
    "location_options": LOCATION_OPTIONS,
  })
  if context:
    ctx.update(context)
  return templates.TemplateResponse(f"partials/{partial_name}.html", ctx)

# --- pages ---
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
  return templates.TemplateResponse("index.html", {"request": request, "todos": TODOS})

@app.get("/account", response_class=HTMLResponse)
async def account_page(request: Request):
  return templates.TemplateResponse("account.html", {"request": request})

@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
  # settings.html includes account_settings by default
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

# --- todos: HTMX endpoints ---
@app.post("/todos", response_class=HTMLResponse)
async def add_todo(request: Request, title: str = Form(...)):
  title = title.strip()
  if title:
    TODOS.append({"id": next(_id_counter), "title": title, "done": False})
  return render_items_fragment(request)

@app.post("/todos/{todo_id}/toggle", response_class=HTMLResponse)
async def toggle_todo(request: Request, todo_id: int):
  for t in TODOS:
    if t["id"] == todo_id:
      t["done"] = not t["done"]
      break
  return render_items_fragment(request)

@app.post("/todos/{todo_id}/delete", response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def delete_todo(request: Request, todo_id: int):
  idx = next((i for i, t in enumerate(TODOS) if t["id"] == todo_id), None)
  if idx is not None:
    TODOS.pop(idx)
  return render_items_fragment(request)

# --- auth partials (from your earlier setup) ---
@app.get("/auth/partials/sign-up", response_class=HTMLResponse)
async def partial_sign_up(request: Request):
  return render_auth_partial(request, "sign_up")

@app.get("/auth/partials/login", response_class=HTMLResponse)
async def partial_login(request: Request):
  return render_auth_partial(request, "login")

@app.get("/auth/partials/forgot", response_class=HTMLResponse)
async def partial_forgot(request: Request):
  return render_auth_partial(request, "forget_password")

# --- settings partials ---
@app.get("/settings/partials/account", response_class=HTMLResponse)
async def partial_account_settings(request: Request):
  return render_settings_partial(request, "account_settings")

@app.get("/settings/partials/agenda", response_class=HTMLResponse)
async def partial_agenda_settings(request: Request):
  return render_settings_partial(request, "agenda_settings")

# --- account settings handlers ---
@app.post("/settings/account/change-email", response_class=HTMLResponse)
async def settings_change_email(
  request: Request,
  current_email: Optional[str] = Form(None),
  new_email: str = Form(...)
):
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
  # In a real app, verify current user and hashed password.
  if len(new_password) < 8:
    return render_settings_partial(request, "account_settings", {"error": "New password must be at least 8 characters."})
  if new_password != confirm_password:
    return render_settings_partial(request, "account_settings", {"error": "Passwords do not match."})
  # Demo accepts anything for old_password
  return render_settings_partial(request, "account_settings", {"success": "Password updated."})

@app.post("/settings/account/delete", response_class=HTMLResponse)
async def settings_delete_account(
  request: Request,
  confirm: Optional[str] = Form(None)
):
  if confirm != "DELETE":
    return render_settings_partial(request, "account_settings", {"error": "Type DELETE to confirm account deletion."})
  # Demo: "delete" resets the demo user
  global CURRENT_EMAIL, USERS, TODOS, AGENDA
  USERS = {}
  CURRENT_EMAIL = None
  TODOS = []  # nuke todos for demo effect
  AGENDA = {
    "agenda_name": "My Daily Feed",
    "subreddit": "lakers",
    "data": {"type": "discussion", "location": "global"},
  }
  return render_settings_partial(request, "account_settings", {"success": "Account deleted (demo)."} )

# --- agenda settings handler ---
@app.post("/settings/agenda/update", response_class=HTMLResponse)
async def settings_agenda_update(
  request: Request,
  agenda_name: str = Form(...),
  subreddit: str = Form(...),
  data_type: str = Form(...),
  data_location: str = Form(...)
):
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

# --- healthcheck ---
@app.get("/healthz")
async def healthz():
  return PlainTextResponse("ok")

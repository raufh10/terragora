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

# --- super simple in-memory stores (demo only) ---
_id_counter = itertools.count(1)
TODOS: List[Dict] = [
  {"id": next(_id_counter), "title": "Ship MVP", "done": False},
  {"id": next(_id_counter), "title": "Write docs", "done": True},
]
USERS: Dict[str, str] = {}  # email -> password (demo only)

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

# --- pages ---
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
  return templates.TemplateResponse("index.html", {"request": request, "todos": TODOS})

@app.get("/account", response_class=HTMLResponse)
async def account_page(request: Request):
  # account.html should include sign_up partial by default as you provided
  return templates.TemplateResponse("account.html", {"request": request})

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

# --- auth: HTMX partial GETs ---
@app.get("/auth/partials/sign-up", response_class=HTMLResponse)
async def partial_sign_up(request: Request):
  return render_auth_partial(request, "sign_up")

@app.get("/auth/partials/login", response_class=HTMLResponse)
async def partial_login(request: Request):
  return render_auth_partial(request, "login")

@app.get("/auth/partials/forgot", response_class=HTMLResponse)
async def partial_forgot(request: Request):
  return render_auth_partial(request, "forget_password")

# --- auth: HTMX POST handlers (demo) ---
@app.post("/auth/sign-up", response_class=HTMLResponse)
async def auth_sign_up(
  request: Request,
  email: str = Form(...),
  password: str = Form(...),
  confirm_password: str = Form(...)
):
  email = email.strip().lower()
  if not EMAIL_RE.match(email):
    return render_auth_partial(request, "sign_up", {"error": "Please enter a valid email."})
  if len(password) < 8:
    return render_auth_partial(request, "sign_up", {"error": "Password must be at least 8 characters."})
  if password != confirm_password:
    return render_auth_partial(request, "sign_up", {"error": "Passwords do not match."})
  if email in USERS:
    return render_auth_partial(request, "sign_up", {"error": "Email already registered. Try logging in."})

  USERS[email] = password  # demo only; do NOT store plain text in real apps
  # On success, return a small success fragment to swap into #account-panel
  return HTMLResponse(
    """
    <div class="card">
      <h3>Welcome!</h3>
      <p class="muted">Account created. You can now log in.</p>
      <div class="mt">
        <button class="btn"
          hx-get="/auth/partials/login"
          hx-target="#account-panel"
          hx-swap="innerHTML">Go to login</button>
      </div>
    </div>
    """,
    status_code=200
  )

@app.post("/auth/login", response_class=HTMLResponse)
async def auth_login(
  request: Request,
  email: str = Form(...),
  password: str = Form(...)
):
  email = email.strip().lower()
  if not EMAIL_RE.match(email):
    return render_auth_partial(request, "login", {"error": "Invalid email."})
  stored = USERS.get(email)
  if not stored or stored != password:
    return render_auth_partial(request, "login", {"error": "Email or password is incorrect."})

  return HTMLResponse(
    """
    <div class="card">
      <h3>Signed in</h3>
      <p class="muted">You’re logged in. This is a demo state only.</p>
    </div>
    """,
    status_code=200
  )

@app.post("/auth/forgot", response_class=HTMLResponse)
async def auth_forgot(
  request: Request,
  email: str = Form(...)
):
  email = email.strip().lower()
  if not EMAIL_RE.match(email):
    return render_auth_partial(request, "forget_password", {"error": "Enter a valid email."})

  # Demo: pretend we emailed a reset link
  return HTMLResponse(
    f"""
    <div class="card">
      <h3>Check your email</h3>
      <p class="muted">If <strong>{email}</strong> exists, a reset link was sent.</p>
      <div class="mt">
        <button class="btn"
          hx-get="/auth/partials/login"
          hx-target="#account-panel"
          hx-swap="innerHTML">Back to login</button>
      </div>
    </div>
    """,
    status_code=200
  )

# --- healthcheck (optional for Railway) ---
@app.get("/healthz")
async def healthz():
  return PlainTextResponse("ok")

from fastapi import APIRouter, Request, Form, Response
from fastapi.responses import HTMLResponse
from app.helpers import templates, render_auth_partial
import os
import httpx

router = APIRouter()

BACKEND_API = os.getenv("BACKEND_API", "http://127.0.0.1:8000")

def _error_fragment(title: str, msg: str) -> str:
  return f"""
  <div class="card soft" style="border-left:3px solid #ef4444; padding-left:1rem;">
    <strong>{title}</strong>
    <p class="muted">{msg}</p>
  </div>
  """

def _success_fragment(title: str, msg: str) -> str:
  return f"""
  <div class="card soft" style="border-left:3px solid #22c55e; padding-left:1rem;">
    <strong>{title}</strong>
    <p class="muted">{msg}</p>
  </div>
  """

@router.get("/account", response_class=HTMLResponse)
async def account_page(request: Request):
  print("[ROUTE] GET /account")
  return templates.TemplateResponse("account.html", {"request": request})

# --------------------------
# Auth partials
# --------------------------
@router.get("/auth/partials/sign-up", response_class=HTMLResponse)
async def partial_sign_up(request: Request):
  print("[ROUTE] GET /auth/partials/sign-up")
  return render_auth_partial(request, "sign_up")

@router.get("/auth/partials/login", response_class=HTMLResponse)
async def partial_login(request: Request):
  print("[ROUTE] GET /auth/partials/login")
  return render_auth_partial(request, "login")

@router.get("/auth/partials/forgot", response_class=HTMLResponse)
async def partial_forgot(request: Request):
  print("[ROUTE] GET /auth/partials/forget_password")
  return render_auth_partial(request, "forget_password")

# --------------------------
# Actions: login / sign-up / signout (via BACKEND_API)
# --------------------------

@router.post("/auth/login", response_class=HTMLResponse)
async def auth_login(
  request: Request,
  response: Response,
  email: str = Form(...),
  password: str = Form(...)
):
  print(f"[ROUTE] POST /auth/login email={email}")
  try:
    async with httpx.AsyncClient(timeout=20) as client:
      r = await client.post(
        f"{BACKEND_API}/account/signin",
        json={"email": email, "password": password},
      )
    if r.status_code >= 400:
      try:
        detail = r.json().get("detail", r.text)
      except Exception:
        detail = r.text
      return HTMLResponse(_error_fragment("Sign in failed", str(detail)))

    data = r.json()
    if not data.get("ok"):
      return HTMLResponse(_error_fragment("Sign in failed", data.get("error", "Unknown error")))
    session = data.get("session", {})
    access_token = session.get("access_token")
    max_age = int(session.get("expires_in", 7 * 24 * 3600))

    if not access_token:
      return HTMLResponse(_error_fragment("Sign in failed", "No access token returned"))

    response.set_cookie(
      key="session",
      value=access_token,
      httponly=True,
      samesite="lax",
      secure=False,
      max_age=max_age,
      path="/",
    )

    html = f"""
    { _success_fragment("Signed in", f"You're signed in as <strong>{email}</strong>.") }
    <div class="row gap mt">
      <a class="btn" href="/settings">Open Settings</a>
      <a class="btn outline" href="/">Go Home</a>
    </div>
    """
    return HTMLResponse(html)

  except Exception as e:
    return HTMLResponse(_error_fragment("Sign in error", str(e)))

@router.post("/auth/sign-up", response_class=HTMLResponse)
async def auth_sign_up(
  request: Request,
  response: Response,
  email: str = Form(...),
  password: str = Form(...),
  confirm_password: str = Form(...)
):
  print(f"[ROUTE] POST /auth/sign-up email={email}")
  if password != confirm_password:
    partial = render_auth_partial(request, "sign_up")
    content = _error_fragment("Error", "Passwords do not match.") + (await partial.body()).decode("utf-8")
    return HTMLResponse(content)

  try:
    async with httpx.AsyncClient(timeout=20) as client:
      r = await client.post(
        f"{BACKEND_API}/account/signup",
        json={"email": email, "password": password},
      )
    if r.status_code >= 400:
      try:
        detail = r.json().get("detail", r.text)
      except Exception:
        detail = r.text
      partial = render_auth_partial(request, "sign_up")
      content = _error_fragment("Sign up failed", str(detail)) + (await partial.body()).decode("utf-8")
      return HTMLResponse(content)

    data = r.json()
    if not data.get("ok"):
      partial = render_auth_partial(request, "sign_up")
      content = _error_fragment("Sign up failed", data.get("error", "Unknown error")) + (await partial.body()).decode("utf-8")
      return HTMLResponse(content)

    session = data.get("session", {})
    access_token = session.get("access_token")
    if access_token:
      response.set_cookie(
        key="session",
        value=access_token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=int(session.get("expires_in", 7 * 24 * 3600)),
        path="/",
      )

    html = f"""
    { _success_fragment("Account created", f"Welcome, <strong>{email}</strong>.") }
    <div class="row gap mt">
      <a class="btn" href="/settings">Open Settings</a>
      <a class="btn outline" href="/">Go Home</a>
    </div>
    """
    return HTMLResponse(html)

  except Exception as e:
    partial = render_auth_partial(request, "sign_up")
    content = _error_fragment("Sign up error", str(e)) + (await partial.body()).decode("utf-8")
    return HTMLResponse(content)

@router.post("/auth/logout", response_class=HTMLResponse)
async def auth_signout(response: Response):
  print("[ROUTE] POST /auth/signout")
  try:
    async with httpx.AsyncClient(timeout=20) as client:
      await client.post(f"{BACKEND_API}/account/signout")
  except Exception as _:
    pass

  response.delete_cookie("session", path="/")

  html = f"""
  { _success_fragment("Signed out", "You have been signed out.") }
  <div class="row gap mt">
    <a class="btn" href="/account">Back to Login</a>
    <a class="btn outline" href="/">Go Home</a>
  </div>
  """
  return HTMLResponse(html)

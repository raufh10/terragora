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
# Actions: login / sign-up / logout (via BACKEND_API)
# --------------------------
@router.post("/auth/login", response_class=HTMLResponse)
async def auth_login(
  request: Request,
  email: str = Form(...),
  password: str = Form(...)
):
  print(f"[ROUTE] POST /auth/login email={email}")
  try:
    async with httpx.AsyncClient(timeout=20) as client:
      r = await client.post(f"{BACKEND_API}/account/signin",
                            json={"email": email, "password": password})
    print(f"[LOGIN] backend status={r.status_code}")
    if r.status_code >= 400:
      try:
        detail = r.json().get("detail", r.text)
      except Exception:
        detail = r.text
      print(f"[LOGIN] backend error detail={detail}")
      return HTMLResponse(_error_fragment("Sign in failed", str(detail)))

    data = r.json()
    print(f"[LOGIN] backend ok={data.get('ok')} keys={list(data.keys())}")
    if not data.get("ok"):
      return HTMLResponse(_error_fragment("Sign in failed", data.get("error", "Unknown error")))

    session = data.get("session", {})
    access_token = session.get("access_token")
    max_age = int(session.get("expires_in", 7 * 24 * 3600))
    print(f"[LOGIN] access_token present={bool(access_token)} max_age={max_age}")

    if not access_token:
      return HTMLResponse(_error_fragment("Sign in failed", "No access token returned"))

    html = f"""
    { _success_fragment("Signed in", f"You're signed in as <strong>{email}</strong>.") }
    <div class="row gap mt">
      <a class="btn" href="/settings">Open Settings</a>
      <a class="btn outline" href="/">Go Home</a>
    </div>
    """
    resp = HTMLResponse(html)
    # IMPORTANT: set cookie on the SAME response object you return
    resp.set_cookie(
      key="session",
      value=access_token,
      httponly=True,
      samesite="lax",
      secure=False,  # True in production (HTTPS)
      max_age=max_age,
      path="/",
    )
    print("[LOGIN] session cookie set on response")
    return resp

  except Exception as e:
    print(f"[LOGIN] exception: {e}")
    return HTMLResponse(_error_fragment("Sign in error", str(e)))


@router.post("/auth/sign-up", response_class=HTMLResponse)
async def auth_sign_up(
  request: Request,
  email: str = Form(...),
  password: str = Form(...),
  confirm_password: str = Form(...)
):
  print(f"[ROUTE] POST /auth/sign-up email={email}")
  if password != confirm_password:
    partial = render_auth_partial(request, "sign_up")
    content = _error_fragment("Error", "Passwords do not match.") + (await partial.body()).decode("utf-8")
    print("[SIGNUP] passwords do not match")
    return HTMLResponse(content)

  try:
    async with httpx.AsyncClient(timeout=20) as client:
      r = await client.post(f"{BACKEND_API}/account/signup",
                            json={"email": email, "password": password})
    print(f"[SIGNUP] backend status={r.status_code}")
    if r.status_code >= 400:
      try:
        detail = r.json().get("detail", r.text)
      except Exception:
        detail = r.text
      print(f"[SIGNUP] backend error detail={detail}")
      partial = render_auth_partial(request, "sign_up")
      content = _error_fragment("Sign up failed", str(detail)) + (await partial.body()).decode("utf-8")
      return HTMLResponse(content)

    data = r.json()
    print(f"[SIGNUP] backend ok={data.get('ok')} keys={list(data.keys())}")
    if not data.get("ok"):
      partial = render_auth_partial(request, "sign_up")
      content = _error_fragment("Sign up failed", data.get("error", "Unknown error")) + (await partial.body()).decode("utf-8")
      return HTMLResponse(content)

    session = data.get("session", {})
    access_token = session.get("access_token")
    max_age = int(session.get("expires_in", 7 * 24 * 3600))
    print(f"[SIGNUP] access_token present={bool(access_token)} max_age={max_age}")

    html = f"""
    { _success_fragment("Account created", f"Welcome, <strong>{email}</strong>.") }
    <div class="row gap mt">
      <a class="btn" href="/settings">Open Settings</a>
      <a class="btn outline" href="/">Go Home</a>
    </div>
    """
    resp = HTMLResponse(html)
    if access_token:
      resp.set_cookie(
        key="session",
        value=access_token,
        httponly=True,
        samesite="lax",
        secure=False,  # True in prod
        max_age=max_age,
        path="/",
      )
      print("[SIGNUP] session cookie set on response")
    return resp

  except Exception as e:
    print(f"[SIGNUP] exception: {e}")
    partial = render_auth_partial(request, "sign_up")
    content = _error_fragment("Sign up error", str(e)) + (await partial.body()).decode("utf-8")
    return HTMLResponse(content)


@router.post("/auth/logout", response_class=HTMLResponse)
async def auth_signout():
  print("[ROUTE] POST /auth/logout")
  # (Optional) call your backend signout
  try:
    async with httpx.AsyncClient(timeout=20) as client:
      r = await client.post(f"{BACKEND_API}/account/signout")
      print(f"[LOGOUT] backend status={r.status_code}")
  except Exception as e:
    print(f"[LOGOUT] backend call failed: {e}")

  html = f"""
  { _success_fragment("Signed out", "You have been signed out.") }
  <div class="row gap mt">
    <a class="btn" href="/account">Back to Login</a>
    <a class="btn outline" href="/">Go Home</a>
  </div>
  """
  resp = HTMLResponse(html)
  # IMPORTANT: delete cookie on the SAME response object you return
  resp.delete_cookie("session", path="/")
  print("[LOGOUT] session cookie deleted on response")
  return resp

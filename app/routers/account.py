from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.helpers import templates, render_auth_partial

router = APIRouter()

@router.get("/account", response_class=HTMLResponse)
async def account_page(request: Request):
  print("[ROUTE] GET /account")
  return templates.TemplateResponse("account.html", {"request": request})

# Auth partials
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

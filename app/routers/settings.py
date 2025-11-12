from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.helpers import templates, AGENDA, CURRENT_EMAIL

router = APIRouter()

@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
  print("[ROUTE] GET /settings")

  # --- Check for session cookie ---
  session_cookie = request.cookies.get("session")
  if session_cookie:
    print(f"[COOKIE] session token found: {session_cookie}")
  else:
    print("[COOKIE] No session cookie found")

  # If you’re actually encoding user_id inside cookie (e.g., JWT):
  # from jose import jwt
  # try:
  #   payload = jwt.decode(session_cookie, "YOUR_SECRET_KEY", algorithms=["HS256"])
  #   user_id = payload.get("sub")
  #   print(f"[COOKIE] user_id: {user_id}")
  # except Exception:
  #   print("[COOKIE] invalid or missing JWT payload")

  return templates.TemplateResponse(
    "settings.html",
    {"request": request, "current_email": CURRENT_EMAIL, "agenda": AGENDA}
  )

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.helpers import templates, AGENDA, CURRENT_EMAIL

router = APIRouter()

@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
  print("[ROUTE] GET /settings")
  return templates.TemplateResponse(
    "settings.html",
    {"request": request, "current_email": CURRENT_EMAIL, "agenda": AGENDA}
  )

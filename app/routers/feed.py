from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse
from app.helpers import templates, MOCK_ITEMS, paginate

router = APIRouter()

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, page: int = Query(1)):
  print(f"[ROUTE] GET /dashboard page={page}")
  items, has_more, next_page = paginate(MOCK_ITEMS, page)
  return templates.TemplateResponse(
    "dashboard.html",
    {"request": request, "items": items, "has_more": has_more, "next_page": next_page}
  )

from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse, PlainTextResponse
from app.helpers import templates, MOCK_ITEMS, paginate

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
  print("[ROUTE] GET /")
  return templates.TemplateResponse("index.html", {"request": request})

@router.get("/dashboard/feed", response_class=HTMLResponse)
async def feed_fragment(request: Request, page: int = Query(1)):
  print(f"[ROUTE] GET /dashboard/feed page={page}")
  items, has_more, next_page = paginate(MOCK_ITEMS, page)
  return templates.TemplateResponse(
    "partials/feed.html",
    {"request": request, "items": items, "has_more": has_more, "next_page": next_page}
  )

@router.get("/healthz")
async def healthz():
  print("[ROUTE] GET /healthz")
  return PlainTextResponse("ok")

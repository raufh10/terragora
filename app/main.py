from fastapi import FastAPI, Request, Form, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List, Dict
import itertools
import os

app = FastAPI(title="FastAPI + Jinja2 + HTMX + Alpine")

# static and templates
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
app.mount("/static", StaticFiles(directory=os.path.join(ROOT_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# super simple in-memory store
_id_counter = itertools.count(1)
TODOS: List[Dict] = [
  {"id": next(_id_counter), "title": "Ship MVP", "done": False},
  {"id": next(_id_counter), "title": "Write docs", "done": True},
]

def render_items_fragment(request: Request) -> HTMLResponse:
  return templates.TemplateResponse(
    "partials/todo_items.html",
    {"request": request, "todos": TODOS}
  )

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
  return templates.TemplateResponse("index.html", {"request": request, "todos": TODOS})

# HTMX endpoints

@app.post("/todos", response_class=HTMLResponse)
async def add_todo(request: Request, title: str = Form(...)):
  title = title.strip()
  if title:
    TODOS.append({"id": next(_id_counter), "title": title, "done": False})
  # return just the list fragment for hx-swap
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

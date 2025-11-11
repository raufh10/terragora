from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os

from app.routers import home, account, settings, feed

app = FastAPI(title="FastAPI + Jinja2 + HTMX + Alpine")

# Static
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
app.mount("/static", StaticFiles(directory=os.path.join(ROOT_DIR, "static")), name="static")

# Routers
app.include_router(home.router)
app.include_router(account.router)
app.include_router(settings.router)
app.include_router(feed.router)

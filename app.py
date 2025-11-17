from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

from contextlib import asynccontextmanager
from services.config import settings
from routers import account, agendas, collect, cookies, label, send, submissions

from logger import start_logger
logger = start_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
  logger.info("🚀 Starting up application...")
  yield
  logger.info("🛑 Shutting down application...")

def create_app() -> FastAPI:
  app = FastAPI(
    title=settings.TITLE,
    version=settings.VERSION,
    description=settings.DESC,
    debug=settings.DEBUG,
    lifespan=lifespan
  )

  # CORS middleware
  app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGIN,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
  )

  # --- Health check route ---
  @app.get("/", tags=["Health"])
  async def root():
    return {
      "ok": True,
      "status": "healthy",
      "title": settings.TITLE,
      "version": settings.VERSION,
      "message": "🚀 API is running smoothly"
    }

  # Register API routers
  app.include_router(account.router, tags=["Auth"])
  app.include_router(agendas.router, tags=["Auth"])
  app.include_router(collect.router, tags=["Extraction"])
  app.include_router(cookies.router, tags=["Auth"])
  app.include_router(label.router, tags=["Transform"])
  app.include_router(send.router, tags=["Load"])
  app.include_router(submissions.router, tags=["Load"])

  # Global exception handler for HTTP errors
  @app.exception_handler(StarletteHTTPException)
  async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    logger.warning(f"HTTP Exception: {exc.detail}")
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

  # Global exception handler for validation errors
  @app.exception_handler(RequestValidationError)
  async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation Error: {exc.errors()}")
    return JSONResponse(status_code=422, content={"detail": exc.errors()})

  return app

app = create_app()

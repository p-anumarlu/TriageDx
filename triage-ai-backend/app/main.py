import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.datastructures import UploadFile as StarletteUploadFile
from starlette.formparsers import MultiPartParser

from app.config import settings
from app.database import init_db
from app.core.limiter import limiter
from app.core.middleware import SecurityMiddleware
from app.routers import (
    assess, auth, history, summary,
    facilities, questions, profile, vision, analytics,
)

logging.basicConfig(
    level=logging.DEBUG if not settings.is_production else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s v%s [%s]", settings.APP_NAME, settings.APP_VERSION, settings.ENVIRONMENT)
    await init_db()
    logger.info("Database initialised")
    yield
    logger.info("Shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Medical triage guidance API — rule + ML + AI engine blend.",
    lifespan=lifespan,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
)

MultiPartParser.max_file_size = 10 * 1024 * 1024   # 10 MB

# ── Rate limiter state ────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── Middleware (order matters — outermost first) ───────────────────────────────
app.add_middleware(SecurityMiddleware)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(assess.router)
app.include_router(auth.router)
app.include_router(history.router)
app.include_router(summary.router)
app.include_router(facilities.router)
app.include_router(questions.router)
app.include_router(profile.router)
app.include_router(vision.router)
app.include_router(analytics.router)


@app.get("/health", tags=["Infra"])
async def health():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }

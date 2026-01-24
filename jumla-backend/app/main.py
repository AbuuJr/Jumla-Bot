"""
app/main.py
FastAPI application entry point with middleware and centralized router registration.
"""
from __future__ import annotations

import logging
import time
from uuid import uuid4
from contextlib import asynccontextmanager
from pathlib import Path
import sys
from typing import Callable

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

# Make imports work regardless of current working directory when running locally
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import settings
from app.core.database import init_db, close_db
from app.dependencies import initialize_ai_services, shutdown_ai_services
from app.api.router_init import include_api_routers  

# Configure logging (simple JSON-like output could be added later)
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("jumla.main")



@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan for startup and shutdown.
    Ensures DB and AI services are initialized at startup and gracefully closed on shutdown.
    """
    logger.info("Starting %s v%s (env=%s)", settings.APP_NAME, settings.VERSION, settings.ENVIRONMENT)

    # Startup sequence (attempt each, but don't crash entire app if non-critical components fail)
    try:
        logger.debug("Initializing database connection...")
        await init_db()
        logger.info("Database initialized")
    except Exception:
        logger.exception("Database initialization failed")
        raise  # DB is critical — re-raise to avoid running without DB

    # Initialize AI services (best-effort)
    try:
        logger.debug("Initializing AI services...")
        await initialize_ai_services()
        logger.info("AI services initialized")
    except Exception:
        logger.exception("AI services failed to initialize; continuing in degraded mode")

    # Place to initialize other optional subsystems (metrics, cache warmups, etc.)

    try:
        yield
    finally:
        # Shutdown sequence (best-effort)
        logger.info("Shutting down application...")
        try:
            await shutdown_ai_services()
            logger.info("AI services shut down")
        except Exception:
            logger.exception("Error shutting down AI services")
        try:
            await close_db()
            logger.info("Database connection closed")
        except Exception:
            logger.exception("Error closing DB connection")


def create_app() -> FastAPI:
    """Factory to create FastAPI app (helps tests and multiple environments)"""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.VERSION,
        description="Backend API for Jumla-bot - Real Estate Lead Management & Automation",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
    )

    # Compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Security headers middleware
    @app.middleware("http")
    async def set_security_headers(request: Request, call_next: Callable):
        response = await call_next(request)
        # Basic security headers; tune according to infra (e.g., HSTS in TLS front-end)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        if settings.ENVIRONMENT == "production":
            response.headers.setdefault("Strict-Transport-Security", "max-age=63072000; includeSubDomains; preload")
        return response

    # Request logging + request id
    @app.middleware("http")
    async def log_requests(request: Request, call_next: Callable):
        request_id = str(uuid4())
        request.state.request_id = request_id
        start = time.time()
        logger.info("[%s] %s %s", request_id, request.method, request.url.path)
        try:
            response = await call_next(request)
        except Exception as exc:
            # Log unexpected exceptions; global handler will format response
            logger.exception("[%s] Unhandled exception during request: %s", request_id, exc)
            raise
        process_time = time.time() - start
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time:.3f}"
        logger.info("[%s] Completed %s %s in %.3fs - status=%s", request_id, request.method, request.url.path, process_time, response.status_code)
        return response

    # Global exception handlers
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": "Validation error",
                "errors": exc.errors(),
                "request_id": getattr(request.state, "request_id", None),
            },
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error", "request_id": getattr(request.state, "request_id", None)},
        )

    # Health and root endpoints (keep these in main for quick checks)
    @app.get("/health", tags=["Health"])
    async def health_check():
        return {
            "status": "healthy",
            "app": settings.APP_NAME,
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
        }

    @app.get("/", tags=["Root"])
    async def root():
        return {
            "app": settings.APP_NAME,
            "version": settings.VERSION,
            "docs": "/docs" if settings.DEBUG else "disabled in production",
        }

    # Register all API routers from a single module
    include_api_routers(app)

    return app


# Create module-level app for Uvicorn
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=1 if settings.DEBUG else settings.WORKERS,
        log_level=settings.LOG_LEVEL.lower(),
    )

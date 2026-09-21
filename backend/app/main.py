from contextlib import asynccontextmanager
import logging
import time
import uuid
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import sentry_sdk

from app.core.config import settings
from app.core.logging import setup_logging
from app.modules.health.routes import router as health_router

setup_logging()
logger = logging.getLogger("zolexora.api")

if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        traces_sample_rate=0.1,
    )

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Zolexora TMS API service...")
    yield
    logger.info("Shutting down Zolexora TMS API service...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
    lifespan=lifespan,
)

# Strict CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time"] = f"{process_time:.2f}ms"
    return response

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    req_id = getattr(request.state, "request_id", "unknown")
    logger.error(f"Unhandled exception [req_id={req_id}]: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Please try again later.",
                "details": {"request_id": req_id} if settings.ENVIRONMENT != "production" else {},
            }
        },
    )

from app.db import models as _db_models  # noqa: F401

# Mount Routers
from app.modules.organisations.routes import router as organisations_router
from app.modules.users.routes import router as users_router
from app.modules.vehicles.routes import router as vehicles_router
from app.modules.bookings.routes_request import router as booking_requests_router
from app.modules.bookings.routes import router as bookings_router
from app.modules.duties.routes import router as duties_router
from app.modules.customization.routes import router as customization_router
from app.modules.billing.routes import router as billing_router
from app.modules.platform.routes import router as platform_router
from app.modules.auth.routes import router as auth_router
from app.modules.extensions.r1rcm.routes import router as r1rcm_router

app.include_router(health_router)
app.include_router(organisations_router)
app.include_router(users_router)
app.include_router(customization_router)
app.include_router(vehicles_router)
app.include_router(booking_requests_router)
app.include_router(bookings_router)
app.include_router(duties_router)
app.include_router(billing_router)
app.include_router(platform_router)
app.include_router(auth_router)
app.include_router(r1rcm_router)

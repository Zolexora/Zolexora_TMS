import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.core.errors import AppError
from app.db.d1_client import D1Client
from app.db.supabase_pg import SupabasePostgres

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("zolexora")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.settings = settings
    app.state.pg = SupabasePostgres(settings.supabase_db_url)
    app.state.d1 = D1Client(settings)
    if settings.supabase_db_url:
        await app.state.pg.connect()
    else:
        logger.warning("SUPABASE_DB_URL not set -- masters endpoints will fail until it is configured.")
    yield
    await app.state.pg.close()
    await app.state.d1.aclose()


app = FastAPI(title="ZolexoraERP API", version="1.0.0", lifespan=lifespan)

_settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request.state.request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    response = await call_next(request)
    response.headers["x-request-id"] = request.state.request_id
    return response


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(status_code=exc.status_code, content=exc.body(request_id))


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    request_id = getattr(request.state, "request_id", None)
    detail = str(exc) if app.state.settings.app_env != "production" else "Internal server error"
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "message": detail, "requestId": request_id},
    )


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "env": app.state.settings.app_env if hasattr(app.state, "settings") else "unknown"}


# --- Routers ---------------------------------------------------------------
from app.modules.auth.routes import router as auth_router  # noqa: E402
from app.modules.companies.routes import router as companies_router  # noqa: E402
from app.modules.sites.routes import router as sites_router  # noqa: E402
from app.modules.clients.routes import router as clients_router  # noqa: E402
from app.modules.periods.routes import router as periods_router  # noqa: E402
from app.modules.pnl_groups.routes import router as pnl_groups_router  # noqa: E402
from app.modules.accounts.routes import router as accounts_router  # noqa: E402
from app.modules.entries.routes import router as entries_router  # noqa: E402
from app.modules.imports.routes import router as imports_router  # noqa: E402
from app.modules.reports.routes import router as reports_router  # noqa: E402
from app.modules.audit.routes import router as audit_router  # noqa: E402
from app.modules.settings.routes import router as settings_router  # noqa: E402

app.include_router(auth_router, prefix="/api")
app.include_router(companies_router, prefix="/api")
app.include_router(sites_router, prefix="/api")
app.include_router(clients_router, prefix="/api")
app.include_router(periods_router, prefix="/api")
app.include_router(pnl_groups_router, prefix="/api")
app.include_router(accounts_router, prefix="/api")
app.include_router(entries_router, prefix="/api")
app.include_router(imports_router, prefix="/api")
app.include_router(reports_router, prefix="/api")
app.include_router(audit_router, prefix="/api")
app.include_router(settings_router, prefix="/api")

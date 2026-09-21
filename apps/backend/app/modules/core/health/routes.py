from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

router = APIRouter(tags=["Health"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {
        "status": "ok",
        "service": "zolexora-tms-api",
        "version": "0.1.0",
    }


@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check(db: AsyncSession = Depends(get_db)):
    db_status = "ok"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "degraded",
                "service": "zolexora-tms-api",
                "database": db_status,
            },
        )

    return {
        "status": "ready",
        "service": "zolexora-tms-api",
        "database": db_status,
    }

import logging
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_organisation, CurrentUserContext
from app.auth.jwks import verify_supabase_jwt
from app.core.websocket import ws_manager
from app.db.session import get_db
from app.modules.duties.models import Duty, DutyStatus
from app.modules.duties.schemas import DutyResponse

logger = logging.getLogger("zolexora.dispatch")
router = APIRouter(tags=["Dispatch"])


@router.get("/api/v1/dispatch/board")
async def get_dispatch_board(
    search: Optional[str] = Query(None, max_length=100),
    ctx: CurrentUserContext = Depends(get_current_active_organisation),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns live duties grouped into the operational dispatch lanes:
    ALLOCATED, DISPATCHED, ARRIVED_PICKUP, IN_TRANSIT, ARRIVED_DROP, DUTY_COMPLETED
    """
    stmt = (
        select(Duty)
        .where(
            Duty.organisation_id == ctx.organisation_id,
            Duty.status != DutyStatus.CANCELLED,
        )
        .order_by(desc(Duty.scheduled_start_time))
        .limit(200)
    )
    res = await db.execute(stmt)
    all_duties = [DutyResponse.model_validate(d) for d in res.scalars().all()]

    board = {
        "ALLOCATED": [],
        "DISPATCHED": [],
        "ARRIVED_PICKUP": [],
        "IN_TRANSIT": [],
        "ARRIVED_DROP": [],
        "DUTY_COMPLETED": [],
    }

    for d in all_duties:
        if d.status.value in board:
            board[d.status.value].append(d)

    return {
        "organisation_id": ctx.organisation_id,
        "total_active": len(all_duties),
        "lanes": board,
    }


@router.websocket("/ws/ops/{org_id}")
async def websocket_ops_endpoint(
    websocket: WebSocket,
    org_id: uuid.UUID,
    token: Optional[str] = Query(None),
):
    """
    Authoritative real-time WebSocket channel for operational transport telemetry.
    Verifies JWT token and tenant ownership before allowing connection.
    """
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        claims = await verify_supabase_jwt(token)
        if not claims.get("sub"):
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    except Exception as e:
        logger.warning(f"WebSocket auth rejected: {e}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await ws_manager.connect(websocket, org_id)
    try:
        while True:
            # Keep socket alive and respond to client pings
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, org_id)
    except Exception as e:
        logger.warning(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket, org_id)

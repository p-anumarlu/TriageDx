from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.database import get_db
from app.models.session import TriageSession
from app.models.user import User
from app.schemas.assess import SessionSummary
from app.core.security import get_current_user

router = APIRouter(prefix="/api/history", tags=["History"])


@router.get("", response_model=list[SessionSummary])
async def get_history(
    session_token: str | None = Query(default=None),
    limit: int = Query(default=20, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
):
    """
    Returns past triage sessions for the current user or anonymous session token.
    Supports both authenticated users and anonymous longitudinal tracking.
    """
    if not current_user and not session_token:
        return []

    conditions = []
    if current_user:
        conditions.append(TriageSession.user_id == current_user.id)
    if session_token:
        conditions.append(TriageSession.session_token == session_token)

    result = await db.execute(
        select(TriageSession)
        .where(or_(*conditions))
        .order_by(TriageSession.created_at.desc())
        .limit(limit)
    )
    sessions = result.scalars().all()

    return [
        SessionSummary(
            session_id=s.id,
            zone_id=s.zone_id,
            triage_level=s.triage_level,
            triage_label=s.triage_label,
            red_flag=s.red_flag,
            created_at=s.created_at.isoformat(),
        )
        for s in sessions
    ]

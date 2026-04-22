from sqlalchemy import String, Integer, Float, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone
import uuid

from app.database import Base


class SessionMetric(Base):
    __tablename__ = "session_metrics"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    zone_id: Mapped[str] = mapped_column(String(50), index=True)
    triage_level: Mapped[int] = mapped_column(Integer, index=True)
    red_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    question_steps: Mapped[int] = mapped_column(Integer, default=0)
    completed: Mapped[bool] = mapped_column(Boolean, default=True)
    used_image: Mapped[bool] = mapped_column(Boolean, default=False)
    used_general: Mapped[bool] = mapped_column(Boolean, default=False)
    rule_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ml_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ai_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    user_age_bucket: Mapped[str | None] = mapped_column(String(10), nullable=True)
    user_sex: Mapped[str | None] = mapped_column(String(10), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )

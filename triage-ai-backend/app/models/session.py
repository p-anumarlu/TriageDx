from sqlalchemy import String, Integer, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
import uuid

from app.database import Base


class TriageSession(Base):
    __tablename__ = "triage_sessions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True, index=True
    )
    session_token: Mapped[str | None] = mapped_column(
        String(36), nullable=True, index=True
    )

    # ── Input ──────────────────────────────────────────────────────────────
    zone_id: Mapped[str] = mapped_column(String(50))
    answers_json: Mapped[dict] = mapped_column(JSON, default=list)
    notes_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Output ─────────────────────────────────────────────────────────────
    triage_level: Mapped[int] = mapped_column(Integer)
    triage_label: Mapped[str] = mapped_column(String(100))
    assessment_text: Mapped[str] = mapped_column(Text)
    treatment_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    red_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)

    # ── Engine telemetry ────────────────────────────────────────────────────
    rule_engine_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ai_engine_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ai_engine_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    possible_conditions_json: Mapped[dict] = mapped_column(JSON, default=list)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )

    user: Mapped["User | None"] = relationship(back_populates="sessions")  # noqa: F821

    def __repr__(self) -> str:
        return f"<TriageSession id={self.id} zone={self.zone_id} level={self.triage_level}>"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    action: Mapped[str] = mapped_column(String(100))
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    session_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    ip_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
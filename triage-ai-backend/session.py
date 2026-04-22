from sqlalchemy import String, Integer, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
import uuid

from app.database import Base


class TriageSession(Base):
    """
    Stores one complete triage assessment flow.
    Supports both authenticated and anonymous (session_token) users.
    Designed for HIPAA: no free-text PII stored in this table.
    """
    __tablename__ = "triage_sessions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    # Nullable — anonymous sessions have no user_id
    user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True, index=True
    )
    # Anonymous tracking token (stored in browser localStorage)
    session_token: Mapped[str | None] = mapped_column(
        String(36), nullable=True, index=True
    )

    # ── Input ──────────────────────────────────────────────────────────────
    zone_id: Mapped[str] = mapped_column(String(50))
    # Stored as JSON list of {question_id, answer_value} dicts
    answers_json: Mapped[dict] = mapped_column(JSON, default=list)

    # ── Output ─────────────────────────────────────────────────────────────
    triage_level: Mapped[int] = mapped_column(Integer)          # 0–4
    triage_label: Mapped[str] = mapped_column(String(100))
    assessment_text: Mapped[str] = mapped_column(Text)
    treatment_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    red_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)

    # ── Engine telemetry (for model retraining) ────────────────────────────
    rule_engine_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ai_engine_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ai_engine_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    possible_conditions_json: Mapped[dict] = mapped_column(JSON, default=list)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )

    # Relationships
    user: Mapped["User | None"] = relationship(back_populates="sessions")  # noqa: F821

    def __repr__(self) -> str:
        return f"<TriageSession id={self.id} zone={self.zone_id} level={self.triage_level}>"


class AuditLog(Base):
    """
    HIPAA-required audit trail. Logs data access and system events.
    IP addresses are hashed — never stored in plaintext.
    """
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    action: Mapped[str] = mapped_column(String(100))           # e.g. "assess.create"
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    session_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    ip_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)  # SHA-256
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )

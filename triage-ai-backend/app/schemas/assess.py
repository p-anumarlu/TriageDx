from pydantic import BaseModel, Field
from typing import Optional
import uuid


# ── Request ──────────────────────────────────────────────────────────────────

class SymptomAnswer(BaseModel):
    """A single Q&A pair from the frontend questionnaire."""
    question_id: str = Field(..., description="ID of the question (e.g. 'sensation')")
    answer_value: str = Field(..., description="Selected answer value (e.g. 'pressure')")


class VisionInput(BaseModel):
    """Vision analysis result forwarded from /api/vision/analyse."""
    urgency_signal: int = Field(..., ge=0, le=4)
    confidence: float = Field(..., ge=0.0, le=1.0)
    red_flag_visible: bool = False
    analysis_available: bool = True


class AssessmentRequest(BaseModel):
    """
    Payload sent by the frontend after the user completes the questionnaire.
    session_token enables anonymous longitudinal tracking (stored in browser).
    """
    zone_id: str = Field(..., description="Body zone tapped by the user")
    answers: list[SymptomAnswer] = Field(..., min_length=1, max_length=10)
    notes: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Free-text additional context from the user (from \'Other\' option).",
    )
    session_token: Optional[str] = Field(
        default=None,
        description="Anonymous tracking UUID from localStorage. "
                    "Omit for fully anonymous (no tracking) sessions."
    )
    vision: Optional[VisionInput] = Field(
        default=None,
        description="Vision analysis result from /api/vision/analyse, if an image was uploaded.",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "zone_id": "chest",
                "answers": [
                    {"question_id": "sensation", "answer_value": "pressure"},
                    {"question_id": "radiation", "answer_value": "cardiac_rad"},
                    {"question_id": "assoc",     "answer_value": "cardiac_assoc"},
                    {"question_id": "onset",     "answer_value": "sudden"},
                    {"question_id": "duration",  "answer_value": "acute"},
                ],
                "session_token": "550e8400-e29b-41d4-a716-446655440000",
                "vision": {
                    "urgency_signal": 3,
                    "confidence": 0.75,
                    "red_flag_visible": False,
                    "analysis_available": True,
                },
            }
        }


# ── Response ─────────────────────────────────────────────────────────────────

class AssessmentResponse(BaseModel):
    """Full triage result returned to the frontend."""
    session_id: str

    # Core result — these drive the UI
    triage_level: int = Field(..., ge=0, le=4, description="0=home ... 4=911")
    triage_label: str
    assessment: str = Field(..., description="Your symptoms may be consistent with...")
    treatment: str = Field(default="", description="OTC/home treatment recommendation from zone flow")
    next_steps: list[str]
    red_flag: bool = Field(..., description="True = 911 interrupt fires immediately")

    # Detail — shown on result screen
    possible_conditions: list[str]
    confidence: float = Field(..., ge=0.0, le=1.0)

    # Engine telemetry — for investor/demo transparency
    rule_engine_level: Optional[int] = None
    ai_engine_level:   Optional[int] = None
    blended: bool = True
    vision_applied: bool = Field(
        default=False,
        description="True if the vision signal influenced the final triage level.",
    )

    # Regulatory
    disclaimer: str = (
        "This tool provides general triage guidance only and does not constitute a "
        "medical diagnosis. Always consult a licensed healthcare provider for medical "
        "advice. If you believe you are experiencing a medical emergency, call 911 immediately."
    )


# ── History ──────────────────────────────────────────────────────────────────

class SessionSummary(BaseModel):
    session_id: str
    zone_id: str
    triage_level: int
    triage_label: str
    red_flag: bool
    created_at: str

    class Config:
        from_attributes = True

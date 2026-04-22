import logging
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.schemas.assess import AssessmentRequest, AssessmentResponse
from app.models.session import TriageSession, AuditLog
from app.models.profile import UserProfile
from app.models.analytics import SessionMetric
from app.models.user import User
from app.services.rule_engine import rule_engine, TRIAGE_LABELS, NEXT_STEPS, LEVEL_911
from app.services.ai_engine import ai_engine
from app.services.ml_engine import ml_engine
from app.services.blender import blend
from app.services.zone_flows import get_flow, traverse
from app.core.security import get_current_user, hash_ip
from app.core.middleware import sanitise_string
from app.schemas.profile import build_profile_context
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/assess", tags=["Assessment"])

_DISCLAIMER = (
    "This tool provides general triage guidance only and does not constitute a "
    "medical diagnosis. Always consult a licensed healthcare provider for medical "
    "advice. If you believe you are experiencing a medical emergency, call 911 immediately."
)


@router.post("", response_model=AssessmentResponse)
async def create_assessment(
    payload: AssessmentRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
):
    # Sanitise all string inputs
    zone       = sanitise_string(payload.zone_id, max_len=50)
    notes_text = sanitise_string(payload.notes, max_len=1000) if payload.notes else None
    answers_list = [
        {
            "question_id": sanitise_string(a.question_id, 100),
            "answer_value": sanitise_string(a.answer_value, 200),
        }
        for a in payload.answers
    ]

    # Fetch profile context if authenticated
    profile_ctx: dict = {}
    if current_user:
        p_result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == current_user.id)
        )
        profile = p_result.scalar_one_or_none()
        ctx = build_profile_context(profile)
        profile_ctx = ctx.model_dump()

    # Zone flow traversal
    flow        = get_flow(zone)
    flow_result = traverse(flow, answers_list)

    # Rule engine (always)
    rule_result = rule_engine.evaluate(zone, answers_list)

    # ML engine (always)
    ml_result = ml_engine.evaluate(zone, answers_list, profile_ctx or None)

    # AI engine (general zone only)
    ai_result = await ai_engine.evaluate(zone, answers_list, extra_context=notes_text)

    # Three-way blend
    blended = blend(zone, rule_result, ml_result, ai_result)

    # Flow red flag overrides
    if flow_result.red_flag:
        final_level    = LEVEL_911
        final_red_flag = True
    else:
        final_level    = max(blended.level, _urgency_to_level(flow_result.urgency_score))
        final_red_flag = blended.red_flag

    # Vision signal merge — must come after flow override so red_flag_visible can still escalate
    final_level, final_red_flag, vision_applied = _apply_vision(
        final_level, final_red_flag, payload.vision
    )

    final_conditions = (
        flow_result.diagnoses if flow_result.diagnoses else blended.conditions
    )

    triage_label   = TRIAGE_LABELS[final_level]
    next_steps     = NEXT_STEPS[final_level]
    treatment_text = flow_result.treatment if flow_result.reached_terminal else ""
    assessment_text = _build_assessment(zone, final_conditions, final_level)

    # Persist session
    session = TriageSession(
        user_id=current_user.id if current_user else None,
        session_token=payload.session_token,
        zone_id=zone,
        answers_json=answers_list,
        notes_text=notes_text,
        triage_level=final_level,
        triage_label=triage_label,
        assessment_text=assessment_text,
        treatment_text=treatment_text,
        red_flag=final_red_flag,
        confidence=blended.confidence,
        rule_engine_level=rule_result.level,
        ai_engine_level=blended.ai_engine_level,
        ai_engine_confidence=blended.ai_engine_confidence,
        possible_conditions_json=final_conditions,
    )
    db.add(session)

    # Analytics metric
    age_bucket = None
    if profile_ctx.get("age"):
        age = profile_ctx["age"]
        if   age < 18: age_bucket = "<18"
        elif age < 35: age_bucket = "18-34"
        elif age < 50: age_bucket = "35-49"
        elif age < 65: age_bucket = "50-64"
        else:          age_bucket = "65+"

    db.add(SessionMetric(
        zone_id=zone,
        triage_level=final_level,
        red_flag=final_red_flag,
        question_steps=len(answers_list),
        completed=flow_result.reached_terminal,
        used_image=payload.vision is not None and payload.vision.analysis_available,
        used_general=(zone == "general"),
        rule_level=rule_result.level,
        ml_level=ml_result.level if not ml_result.fallback else None,
        ai_level=blended.ai_engine_level,
        confidence=blended.confidence,
        user_age_bucket=age_bucket,
        user_sex=profile_ctx.get("biological_sex"),
    ))

    await db.flush()

    # HIPAA audit
    if settings.HIPAA_AUDIT_LOG:
        client_ip = request.client.host if request.client else "unknown"
        db.add(AuditLog(
            action="assess.create",
            user_id=current_user.id if current_user else None,
            session_id=session.id,
            ip_hash=hash_ip(client_ip),
            details=f"zone={zone} level={final_level} red_flag={final_red_flag} vision_applied={vision_applied}",
        ))

    await db.commit()

    return AssessmentResponse(
        session_id=session.id,
        triage_level=final_level,
        triage_label=triage_label,
        assessment=assessment_text,
        treatment=treatment_text,
        next_steps=next_steps,
        red_flag=final_red_flag,
        possible_conditions=final_conditions,
        confidence=blended.confidence,
        rule_engine_level=rule_result.level,
        ai_engine_level=blended.ai_engine_level,
        blended=blended.blended,
        vision_applied=vision_applied,
        disclaimer=_DISCLAIMER,
    )


def _apply_vision(
    base_level: int,
    base_red_flag: bool,
    vision,
) -> tuple[int, bool, bool]:
    """
    Merge vision urgency signal into the questionnaire-derived level.
    Returns (final_level, final_red_flag, vision_applied).

    Decision matrix:
      confidence < 0.4         -> ignore entirely
      red_flag_visible = True  -> always escalate to LEVEL_911
      confidence >= 0.6        -> take max(base, vision) unconditionally
      confidence 0.4–0.6       -> take max only if vision exceeds base by > 1 level
                                  (prevents marginal low-confidence escalations)
    """
    if vision is None or not vision.analysis_available:
        return base_level, base_red_flag, False

    if vision.confidence < 0.4:
        logger.debug("Vision confidence %.2f below threshold — ignored", vision.confidence)
        return base_level, base_red_flag, False

    if vision.red_flag_visible:
        logger.info("Vision red flag visible — escalating to LEVEL_911")
        return LEVEL_911, True, True

    v               = vision.urgency_signal
    high_confidence = vision.confidence >= 0.6
    big_gap         = v > base_level + 1

    if high_confidence or big_gap:
        merged = max(base_level, v)
        if merged != base_level:
            logger.info(
                "Vision escalated: base=%d vision=%d conf=%.2f -> %d",
                base_level, v, vision.confidence, merged,
            )
            return merged, base_red_flag or (merged >= LEVEL_911), True
        # Vision agreed with or was below base — applied but no change
        return base_level, base_red_flag, True

    logger.debug(
        "Vision signal %d conf %.2f insufficient to override base %d",
        v, vision.confidence, base_level,
    )
    return base_level, base_red_flag, False


def _urgency_to_level(score: int) -> int:
    if score <= 0: return 0
    if score <= 2: return 1
    if score <= 5: return 2
    if score <= 9: return 3
    return 4


def _build_assessment(zone: str, conditions: list[str], level: int) -> str:
    zone_label = zone.replace("_", " ")
    if not conditions or conditions[0].startswith("Symptom pattern"):
        return (
            f"Your symptoms in the {zone_label} area may warrant clinical evaluation. "
            "Please review the recommended next steps."
        )
    primary = conditions[0]
    if level <= 1:
        return f"Your symptoms may be consistent with {primary}. This presentation appears manageable at home or with over-the-counter care."
    if level == 2:
        return f"Your symptoms may be consistent with {primary}. A clinician should evaluate you to confirm and recommend treatment."
    if level == 3:
        return f"Your symptoms may be consistent with {primary}. This warrants same-day emergency evaluation."
    return f"Your symptoms may be consistent with {primary}. This may be a life-threatening emergency — do not delay."
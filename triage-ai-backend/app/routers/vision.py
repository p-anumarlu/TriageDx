import base64
import logging
import re
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional

from app.core.security import get_current_user
from app.core.limiter import limiter, UPLOAD_LIMIT
from app.core.middleware import sanitise_string
from app.models.user import User
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/vision", tags=["Vision"])

_ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp", "image/heic"}
_MAX_BYTES = 8 * 1024 * 1024  # 8 MB

_VISION_PROMPT = """You are a clinical image analysis assistant embedded in a medical triage tool.
Analyse this patient-submitted image and return ONLY valid JSON:
{
  "visible_findings": ["<finding 1>", "<finding 2>"],
  "possible_conditions": ["<condition 1>", "<condition 2>"],
  "urgency_signal": <integer 0-4>,
  "confidence": <float 0.0-1.0>,
  "red_flag_visible": <true|false>,
  "reasoning": "<1 sentence>"
}

urgency_signal scale: 0=home care, 1=OTC, 2=doctor, 3=ER, 4=911.
red_flag_visible: true ONLY for visible signs of life-threatening emergency
(e.g. severe burns, obvious arterial bleeding, anaphylaxis swelling).
Be conservative. Image analysis is supplementary — never the sole basis for diagnosis.
If the image is not medically relevant or cannot be assessed, return urgency_signal=2
and confidence=0.3."""


class VisionResult(BaseModel):
    visible_findings: list[str] = []
    possible_conditions: list[str] = []
    urgency_signal: int = 2
    confidence: float = 0.3
    red_flag_visible: bool = False
    reasoning: str = ""
    analysis_available: bool = True


@router.post("/analyse", response_model=VisionResult)
@limiter.limit(UPLOAD_LIMIT)
async def analyse_image(
    request: Request,
    file: UploadFile = File(...),
    zone_id: str = Form(default="unknown"),
    current_user: Optional[User] = Depends(get_current_user),
):
    # Validate file 
    content_type = file.content_type or ""
    if content_type not in _ALLOWED_MIME:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported image type '{content_type}'. Use JPEG, PNG, WebP, or HEIC.",
        )

    data = await file.read()
    if len(data) > _MAX_BYTES:
        raise HTTPException(status_code=413, detail="Image exceeds 8 MB limit.")

    if not settings.GOOGLE_AI_API_KEY:
        logger.warning("Vision analysis requested but GOOGLE_AI_API_KEY not set")
        return VisionResult(
            visible_findings=[],
            possible_conditions=[],
            urgency_signal=2,
            confidence=0.3,
            red_flag_visible=False,
            reasoning="Vision analysis unavailable — AI key not configured.",
            analysis_available=False,
        )

    try:
        import google.generativeai as genai

        genai.configure(api_key=settings.GOOGLE_AI_API_KEY)
        model = genai.GenerativeModel(
            model_name=settings.GEMINI_MODEL,  # ← use your .env model
            generation_config=genai.GenerationConfig(
                temperature=0.1,
                max_output_tokens=512,
            ),
        )

        mime = content_type.split(";")[0].strip()

        response = await model.generate_content_async([
            _VISION_PROMPT + f"\n\nBody zone: {sanitise_string(zone_id, 50)}",
            {"mime_type": mime, "data": data},  # ← raw bytes, not base64
        ])

        raw = response.text
        clean = re.sub(r"```(?:json)?|```", "", raw).strip()

        import json
        parsed = json.loads(clean)

        return VisionResult(
            visible_findings=parsed.get("visible_findings", [])[:6],
            possible_conditions=parsed.get("possible_conditions", [])[:4],
            urgency_signal=max(0, min(4, int(parsed.get("urgency_signal", 2)))),
            confidence=float(parsed.get("confidence", 0.3)),
            red_flag_visible=bool(parsed.get("red_flag_visible", False)),
            reasoning=str(parsed.get("reasoning", "")),
            analysis_available=True,
        )

    except Exception as exc:
        logger.error("Vision analysis error: %s", exc)
        return VisionResult(
            visible_findings=[],
            possible_conditions=[],
            urgency_signal=2,
            confidence=0.25,
            red_flag_visible=False,
            reasoning="Image analysis encountered an error. Symptom questionnaire result is authoritative.",
            analysis_available=False,
        )

"""
Google AI Studio — Gemini Triage Engine
"""
import json
import logging
import re
from dataclasses import dataclass
from typing import Optional

try:
    import google.generativeai as genai
    _GENAI_AVAILABLE = True
except ImportError:
    genai = None
    _GENAI_AVAILABLE = False

from app.config import settings
from app.services.rule_engine import LEVEL_HOME, LEVEL_911

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a clinical triage decision support system embedded in a consumer health app.
Your job is to analyze patient-reported symptoms and recommend an appropriate level of care.

You are NOT a diagnostic tool. You must never provide a definitive diagnosis.
You must always default to the MORE CONSERVATIVE (higher urgency) level when uncertain.

OUTPUT FORMAT — return ONLY valid JSON, no markdown, no explanation outside the JSON:
{
  "triage_level": <integer 0-4>,
  "confidence": <float 0.0-1.0>,
  "possible_conditions": ["<condition 1>", "<condition 2>"],
  "reasoning": "<1-2 sentence clinical reasoning>",
  "red_flag_detected": <true|false>
}

TRIAGE LEVELS:
  0 = Manage at home  (self-care sufficient)
  1 = OTC + monitor   (pharmacy-level care)
  2 = Doctor / urgent care  (within hours today)
  3 = ER same-day     (within 1-2 hours)
  4 = Call 911 now    (life-threatening, minutes matter)

HARD RULES — these override all other considerations:
- Level 4 (red_flag_detected: true) is MANDATORY for any of:
    suspected MI / ACS, stroke / TIA, subarachnoid hemorrhage,
    bacterial meningitis, aortic dissection, anaphylaxis,
    tension pneumothorax, upper GI hemorrhage, bowel perforation,
    acute limb ischemia, respiratory failure.
- When in doubt between two levels, always choose the higher (more urgent) one.
- Never recommend level 0 or 1 for chest pain or neurological symptoms
  unless the presentation is clearly musculoskeletal or positional.
"""


@dataclass
class AIEngineResult:
    level: int
    confidence: float
    red_flag: bool
    conditions: list[str]
    reasoning: str
    error: Optional[str] = None
    fallback: bool = False


class GeminiTriageEngine:

    def __init__(self) -> None:
        if _GENAI_AVAILABLE and settings.GOOGLE_AI_API_KEY:
            genai.configure(api_key=settings.GOOGLE_AI_API_KEY)
            self._model = genai.GenerativeModel(
                model_name=settings.GEMINI_MODEL,
                system_instruction=_SYSTEM_PROMPT,
                generation_config=genai.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=512,
                ),
            )
        else:
            self._model = None
            if not _GENAI_AVAILABLE:
                logger.warning("google-generativeai not installed — run: pip install google-generativeai")
            else:
                logger.warning(
                    "GOOGLE_AI_API_KEY not set — AI engine will return fallback results. "
                    "Add your key to .env to enable Gemini triage."
                )

    async def evaluate(self, zone_id: str, answers: list[dict], extra_context: str | None = None) -> AIEngineResult:
        if self._model is None:
            return self._no_api_key_fallback()

        prompt = self._build_prompt(zone_id, answers, extra_context)

        try:
            response = await self._model.generate_content_async(prompt)
            return self._parse_response(response.text)
        except Exception as exc:
            logger.error("Gemini API error: %s", exc)
            return AIEngineResult(
                level=LEVEL_911,
                confidence=0.50,
                red_flag=False,
                conditions=[],
                reasoning="AI engine unavailable — rule engine result used exclusively.",
                error=str(exc),
                fallback=True,
            )
    
    async def evaluate_image(
        self,
        zone_id: str,
        image_bytes: bytes,
        mime_type: str = "image/jpeg",
        extra_context: str | None = None,
    ) -> AIEngineResult:
        if self._model is None:
            return self._no_api_key_fallback()

        prompt_text = (
            f"Body zone: {zone_id}\n"
            f"The patient has uploaded a photo of their affected area.\n"
        )
        if extra_context:
            prompt_text += f"Patient's description: {extra_context}\n"
        prompt_text += (
            "\nAnalyze the image for any visible clinical findings "
            "(rash, swelling, discoloration, wound, lesion, etc.) "
            "and assess the appropriate triage level. "
            "If the image is unclear or non-diagnostic, default to a conservative level."
        )

        import google.generativeai as genai_lib
        image_part = {"mime_type": mime_type, "data": image_bytes}

        try:
            response = await self._model.generate_content_async([prompt_text, image_part])
            result = self._parse_response(response.text)
            return result
        except Exception as exc:
            logger.error("Gemini image analysis error: %s", exc)
            return AIEngineResult(
                level=2,
                confidence=0.0,
                red_flag=False,
                conditions=[],
                reasoning="Image analysis failed — symptom questions are authoritative.",
                error=str(exc),
                fallback=True,
            )

    @staticmethod
    def _build_prompt(zone_id: str, answers: list[dict], extra_context: str | None = None) -> str:
        qa_lines = "\n".join(
            f"  Q({a['question_id']}): {a['answer_value']}" for a in answers
        )
        prompt = (
            f"Body zone: {zone_id}\n"
            f"Patient answers:\n{qa_lines}\n"
        )
        if extra_context:
            prompt += f"\nPatient's own description: {extra_context}\n"
        prompt += "\nAssess the triage level for this presentation."
        return prompt

    @staticmethod
    def _parse_response(raw: str) -> AIEngineResult:
        clean = re.sub(r"```(?:json)?|```", "", raw).strip()
        try:
            data = json.loads(clean)
        except json.JSONDecodeError:
            logger.error("Failed to parse Gemini JSON: %s", raw[:200])
            return AIEngineResult(
                level=LEVEL_911,
                confidence=0.50,
                red_flag=False,
                conditions=[],
                reasoning="AI engine returned unparseable response.",
                error="JSONDecodeError",
                fallback=True,
            )

        level = int(data.get("triage_level", LEVEL_911))
        level = max(LEVEL_HOME, min(LEVEL_911, level))

        return AIEngineResult(
            level=level,
            confidence=float(data.get("confidence", 0.5)),
            red_flag=bool(data.get("red_flag_detected", False)),
            conditions=list(data.get("possible_conditions", [])),
            reasoning=str(data.get("reasoning", "")),
        )

    @staticmethod
    def _no_api_key_fallback() -> AIEngineResult:
        return AIEngineResult(
            level=2,
            confidence=0.40,
            red_flag=False,
            conditions=["AI engine offline — rule engine result is authoritative"],
            reasoning="Google AI key not configured. Rule engine result used.",
            error="GOOGLE_AI_API_KEY not set",
            fallback=True,
        )


ai_engine = GeminiTriageEngine()
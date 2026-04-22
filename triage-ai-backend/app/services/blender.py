"""
Three-way Confidence-Weighted Ensemble Blender
───────────────────────────────────────────────
Combines: rule engine + ML engine + Gemini AI engine (general zone only).

Conservative bias rules (in priority order):
  1. Any engine detects red_flag → 911 immediately.
  2. AI engine fallback → exclude from blend.
  3. ML engine fallback → use rule + AI only.
  4. Weighted blend of available engines.
  5. Rule engine is the hard floor — cannot be downgraded.
  6. Zone-specific urgency floors enforced.
  7. On large divergence (>1 level), take the maximum.
"""
import math
import logging
from dataclasses import dataclass

from app.services.rule_engine import RuleResult, LEVEL_911, TRIAGE_LABELS, NEXT_STEPS
from app.services.ai_engine import AIEngineResult
from app.services.ml_engine import MLResult

logger = logging.getLogger(__name__)

_ZONE_FLOOR = {"chest": 2, "head": 1}

# Engine weights for the ensemble
_W_RULE = 0.45
_W_ML   = 0.30
_W_AI   = 0.25


@dataclass
class BlendedResult:
    level: int
    confidence: float
    red_flag: bool
    conditions: list[str]
    reasoning: str
    triage_label: str
    next_steps: list[str]
    rule_engine_level: int
    ml_engine_level: int | None
    ai_engine_level: int | None
    ai_engine_confidence: float | None
    blended: bool


def blend(
    zone_id: str,
    rule_result: RuleResult,
    ml_result: MLResult,
    ai_result: AIEngineResult,
) -> BlendedResult:

    # 1. Red flag hard override
    if rule_result.red_flag or ai_result.red_flag:
        return _make(
            level=LEVEL_911, confidence=max(rule_result.confidence, ai_result.confidence),
            red_flag=True,
            conditions=_merge(rule_result.conditions, ml_result.diagnoses, ai_result.conditions),
            reasoning=rule_result.reasoning or ai_result.reasoning,
            rule_l=rule_result.level, ml_l=ml_result.level, ai_l=ai_result.level,
            ai_conf=ai_result.confidence, blended=True,
        )

    # Build active engines list
    engines: list[tuple[float, float, int]] = []  # (weight, confidence, level)
    engines.append((_W_RULE, rule_result.confidence, rule_result.level))

    if not ml_result.fallback:
        engines.append((_W_ML, ml_result.confidence, ml_result.level))

    if not ai_result.fallback:
        engines.append((_W_AI, ai_result.confidence, ai_result.level))

    # 2. Only rule engine active
    if len(engines) == 1:
        return _make(
            level=rule_result.level, confidence=rule_result.confidence,
            red_flag=False,
            conditions=_merge(rule_result.conditions, ml_result.diagnoses, []),
            reasoning=rule_result.reasoning,
            rule_l=rule_result.level, ml_l=ml_result.level, ai_l=ai_result.level,
            ai_conf=ai_result.confidence, blended=False,
        )

    # 3. Confidence-weighted blend
    total_w = sum(w * c for w, c, _ in engines)
    total_w = total_w if total_w > 0 else 1.0
    weighted_level = sum(w * c * l for w, c, l in engines) / total_w
    blended_level = math.ceil(weighted_level)

    # 4. Large divergence — take maximum
    all_levels = [l for _, _, l in engines]
    if max(all_levels) - min(all_levels) > 1:
        blended_level = max(all_levels)

    # 5. Rule engine is the floor
    blended_level = max(blended_level, rule_result.level)

    # 6. Zone floor
    blended_level = max(blended_level, _ZONE_FLOOR.get(zone_id, 0))
    blended_level = max(0, min(4, blended_level))

    # Blended confidence
    blended_conf = sum(w * c for w, c, _ in engines) / sum(w for w, _, _ in engines)

    conditions = _merge(rule_result.conditions, ml_result.diagnoses, ai_result.conditions)
    reasoning = _merge_reasoning(rule_result.reasoning, ml_result.reasoning, ai_result.reasoning)

    return _make(
        level=blended_level, confidence=round(blended_conf, 3),
        red_flag=False, conditions=conditions, reasoning=reasoning,
        rule_l=rule_result.level, ml_l=ml_result.level, ai_l=ai_result.level,
        ai_conf=ai_result.confidence, blended=True,
    )


def _make(level, confidence, red_flag, conditions, reasoning,
          rule_l, ml_l, ai_l, ai_conf, blended) -> BlendedResult:
    return BlendedResult(
        level=level, confidence=confidence, red_flag=red_flag,
        conditions=conditions, reasoning=reasoning,
        triage_label=TRIAGE_LABELS[level], next_steps=NEXT_STEPS[level],
        rule_engine_level=rule_l, ml_engine_level=ml_l,
        ai_engine_level=ai_l, ai_engine_confidence=ai_conf, blended=blended,
    )


def _merge(*lists: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for lst in lists:
        for item in lst:
            if item and item not in seen:
                seen.add(item)
                out.append(item)
    return out[:5]


def _merge_reasoning(*args: str) -> str:
    parts = [a.strip() for a in args if a and a.strip()]
    return " | ".join(parts[:2])

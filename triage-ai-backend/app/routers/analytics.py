from collections import defaultdict
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.database import get_db
from app.models.analytics import SessionMetric
from app.core.limiter import limiter, ANALYTICS_LIMIT

router = APIRouter(prefix="/admin/analytics", tags=["Analytics"])


@router.get("")
@limiter.limit(ANALYTICS_LIMIT)
async def get_analytics(
    request: Request,
    days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    since = datetime.now(timezone.utc) - timedelta(days=days)

    result = await db.execute(
        select(SessionMetric).where(SessionMetric.created_at >= since)
    )
    metrics: list[SessionMetric] = list(result.scalars().all())

    if not metrics:
        return _empty_response(days)

    total = len(metrics)
    completed = sum(1 for m in metrics if m.completed)
    red_flags = sum(1 for m in metrics if m.red_flag)
    used_image = sum(1 for m in metrics if m.used_image)

    # Zone distribution
    zone_counts: dict[str, int] = defaultdict(int)
    for m in metrics:
        zone_counts[m.zone_id] += 1

    # Triage level distribution
    level_counts: dict[int, int] = defaultdict(int)
    for m in metrics:
        level_counts[m.triage_level] += 1

    # Average steps per zone
    zone_steps: dict[str, list[int]] = defaultdict(list)
    for m in metrics:
        zone_steps[m.zone_id].append(m.question_steps)
    avg_steps = {z: round(sum(s) / len(s), 1) for z, s in zone_steps.items()}

    # Confidence stats
    confidences = [m.confidence for m in metrics if m.confidence > 0]
    avg_confidence = round(sum(confidences) / len(confidences), 3) if confidences else 0

    # Engine divergence (rule vs ML)
    divergence = [
        abs((m.rule_level or 0) - (m.ml_level or 0))
        for m in metrics
        if m.rule_level is not None and m.ml_level is not None
    ]
    avg_divergence = round(sum(divergence) / len(divergence), 2) if divergence else 0

    # Age bucket breakdown
    age_breakdown: dict[str, int] = defaultdict(int)
    for m in metrics:
        if m.user_age_bucket:
            age_breakdown[m.user_age_bucket] += 1

    # Sex breakdown
    sex_breakdown: dict[str, int] = defaultdict(int)
    for m in metrics:
        if m.user_sex:
            sex_breakdown[m.user_sex] += 1

    # Top zones by red flag rate
    zone_rf: dict[str, list[bool]] = defaultdict(list)
    for m in metrics:
        zone_rf[m.zone_id].append(m.red_flag)
    zone_rf_rate = {
        z: round(sum(flags) / len(flags), 3)
        for z, flags in zone_rf.items()
    }
    top_rf_zones = sorted(zone_rf_rate.items(), key=lambda x: -x[1])[:5]

    return {
        "period_days": days,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_sessions": total,
            "completion_rate": round(completed / total, 3),
            "red_flag_rate": round(red_flags / total, 3),
            "image_upload_rate": round(used_image / total, 3),
            "avg_confidence": avg_confidence,
            "avg_engine_divergence_levels": avg_divergence,
        },
        "triage_level_distribution": {
            str(k): {"count": v, "pct": round(v / total, 3)}
            for k, v in sorted(level_counts.items())
        },
        "zone_distribution": dict(
            sorted(zone_counts.items(), key=lambda x: -x[1])[:15]
        ),
        "avg_steps_per_zone": avg_steps,
        "top_red_flag_zones": dict(top_rf_zones),
        "demographic_breakdown": {
            "age_buckets": dict(age_breakdown),
            "biological_sex": dict(sex_breakdown),
        },
        "data_notice": (
            "All metrics are anonymous and aggregate. "
            "No personally identifiable information is included in this report."
        ),
    }


def _empty_response(days: int) -> dict:
    return {
        "period_days": days,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {"total_sessions": 0},
        "triage_level_distribution": {},
        "zone_distribution": {},
        "avg_steps_per_zone": {},
        "top_red_flag_zones": {},
        "demographic_breakdown": {"age_buckets": {}, "biological_sex": {}},
        "data_notice": "No sessions recorded in the selected period.",
    }

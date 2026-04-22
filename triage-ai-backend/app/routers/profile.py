from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.profile import UserProfile
from app.models.user import User
from app.schemas.profile import ProfileCreate, ProfileOut
from app.core.security import require_user
from app.core.limiter import limiter, AUTH_LIMIT

router = APIRouter(prefix="/api/profile", tags=["Profile"])


@router.get("", response_model=ProfileOut)
async def get_profile(
    current_user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found. Complete onboarding first.")
    return profile


@router.post("", response_model=ProfileOut, status_code=201)
@router.put("", response_model=ProfileOut)
async def upsert_profile(
    payload: ProfileCreate,
    current_user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()

    if profile:
        profile.age = payload.age
        profile.biological_sex = payload.biological_sex
        profile.allergies = payload.allergies
        profile.chronic_conditions = payload.chronic_conditions
        profile.current_medications = payload.current_medications
        profile.past_surgeries = payload.past_surgeries
        profile.onboarding_complete = True
    else:
        profile = UserProfile(
            user_id=current_user.id,
            age=payload.age,
            biological_sex=payload.biological_sex,
            allergies=payload.allergies,
            chronic_conditions=payload.chronic_conditions,
            current_medications=payload.current_medications,
            past_surgeries=payload.past_surgeries,
            onboarding_complete=True,
        )
        db.add(profile)

    await db.commit()
    await db.refresh(profile)
    return profile

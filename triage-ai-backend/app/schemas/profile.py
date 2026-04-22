from pydantic import BaseModel, Field
from typing import Optional


class ProfileCreate(BaseModel):
    age: Optional[int] = Field(default=None, ge=1, le=120)
    biological_sex: Optional[str] = Field(default=None, pattern="^(male|female|other)$")
    allergies: list[str] = Field(default_factory=list, max_length=50)
    chronic_conditions: list[str] = Field(default_factory=list, max_length=50)
    current_medications: list[str] = Field(default_factory=list, max_length=50)
    past_surgeries: list[str] = Field(default_factory=list, max_length=50)

    class Config:
        json_schema_extra = {
            "example": {
                "age": 42,
                "biological_sex": "female",
                "allergies": ["penicillin", "sulfa drugs"],
                "chronic_conditions": ["type 2 diabetes", "hypertension"],
                "current_medications": ["metformin 500mg", "lisinopril 10mg"],
                "past_surgeries": ["appendectomy 2015"],
            }
        }


class ProfileOut(BaseModel):
    age: Optional[int] = None
    biological_sex: Optional[str] = None
    allergies: list[str] = []
    chronic_conditions: list[str] = []
    current_medications: list[str] = []
    past_surgeries: list[str] = []
    onboarding_complete: bool = False

    class Config:
        from_attributes = True


class ProfileContext(BaseModel):
    age: Optional[int] = None
    biological_sex: Optional[str] = None
    has_allergies: bool = False
    chronic_condition_count: int = 0
    on_medications: bool = False
    high_risk_conditions: list[str] = []


HIGH_RISK = {
    "diabetes", "type 2 diabetes", "type 1 diabetes",
    "hypertension", "heart disease", "coronary artery disease",
    "copd", "asthma", "chronic kidney disease", "immunocompromised",
    "cancer", "hiv", "liver disease", "heart failure",
}


def build_profile_context(profile: "UserProfile | None") -> ProfileContext:  # noqa: F821
    if not profile:
        return ProfileContext()
    conditions_lower = [c.lower() for c in (profile.chronic_conditions or [])]
    high_risk = [c for c in conditions_lower if any(h in c for h in HIGH_RISK)]
    return ProfileContext(
        age=profile.age,
        biological_sex=profile.biological_sex,
        has_allergies=bool(profile.allergies),
        chronic_condition_count=len(profile.chronic_conditions or []),
        on_medications=bool(profile.current_medications),
        high_risk_conditions=high_risk,
    )

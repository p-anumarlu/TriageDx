from pydantic import BaseModel


class VisitSummary(BaseModel):
    session_id: str
    generated_at: str
    body_area: str
    main_complaint: str
    symptom_path: list[str]
    red_flags_detected: list[str]
    possible_conditions: list[str]
    treatment_recommendation: str
    triage_level: int
    triage_label: str
    timestamp: str
    plain_text: str
    disclaimer: str

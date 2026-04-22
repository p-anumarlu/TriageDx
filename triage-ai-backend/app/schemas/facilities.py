from pydantic import BaseModel
from typing import Optional


class Facility(BaseModel):
    name: str
    address: str
    phone: Optional[str] = None
    distance_km: float
    facility_type: str
    lat: float
    lng: float
    place_id: Optional[str] = None
    maps_url: Optional[str] = None
    open_now: Optional[bool] = None


class FacilitiesResponse(BaseModel):
    triage_level: int
    facility_type_label: str
    facilities: list[Facility]
    source: str

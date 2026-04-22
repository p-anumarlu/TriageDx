from fastapi import APIRouter, HTTPException
from app.services.zone_flows import get_flow_as_dict, ZONE_FLOWS

router = APIRouter(prefix="/api/questions", tags=["Questions"])

@router.get("/{zone_id}")
async def get_questions(zone_id: str):
    if zone_id not in ZONE_FLOWS:
        raise HTTPException(status_code=404, detail=f"Unknown zone: {zone_id}")
    return {"zone_id": zone_id, "flow": get_flow_as_dict(zone_id)}

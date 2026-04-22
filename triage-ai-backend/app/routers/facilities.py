import math
import logging
from typing import Optional

import httpx
from fastapi import APIRouter, Query, HTTPException

from app.config import settings
from app.schemas.facilities import Facility, FacilitiesResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/facilities", tags=["Facilities"])

_TYPE_MAP = {
    0: ("pharmacy", ["pharmacy"], "Pharmacy / Home Care"),
    1: ("pharmacy", ["pharmacy"], "Pharmacy / Home Care"),
    2: ("clinic",   ["doctor", "health"], "Clinic or Physician"),
    3: ("urgent_care", ["hospital", "doctor", "health"], "Urgent Care or ER"),
    4: ("hospital",  ["hospital"], "Emergency Room"),
}

_PLACES_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
_OVERPASS_URL = "https://overpass-api.de/api/interpreter"


@router.get("", response_model=FacilitiesResponse)
async def get_facilities(
    lat: float = Query(...),
    lng: float = Query(...),
    triage_level: int = Query(..., ge=0, le=4),
    radius_m: int = Query(default=8000, le=25000),
):
    fac_type, _, label = _TYPE_MAP[triage_level]

    if settings.GOOGLE_MAPS_API_KEY:
        facilities = await _google_places(lat, lng, triage_level, radius_m)
        source = "Google Places"
    else:
        facilities = await _overpass(lat, lng, triage_level, radius_m)
        source = "OpenStreetMap"

    facilities.sort(key=lambda f: f.distance_km)
    return FacilitiesResponse(
        triage_level=triage_level,
        facility_type_label=label,
        facilities=facilities[:10],
        source=source,
    )


async def _google_places(lat: float, lng: float, level: int, radius: int) -> list[Facility]:
    _, types, _ = _TYPE_MAP[level]
    results = []
    async with httpx.AsyncClient(timeout=8) as client:
        for ptype in types[:2]:
            try:
                r = await client.get(_PLACES_URL, params={
                    "location": f"{lat},{lng}",
                    "radius": radius,
                    "type": ptype,
                    "key": settings.GOOGLE_MAPS_API_KEY,
                })
                data = r.json()
                for p in data.get("results", [])[:6]:
                    loc = p["geometry"]["location"]
                    dist = _haversine(lat, lng, loc["lat"], loc["lng"])
                    phone = p.get("formatted_phone_number")
                    results.append(Facility(
                        name=p.get("name", "Unknown"),
                        address=p.get("vicinity", ""),
                        phone=phone,
                        distance_km=round(dist, 2),
                        facility_type=ptype,
                        lat=loc["lat"],
                        lng=loc["lng"],
                        place_id=p.get("place_id"),
                        maps_url=f"https://www.google.com/maps/place/?q=place_id:{p.get('place_id','')}",
                        open_now=p.get("opening_hours", {}).get("open_now"),
                    ))
            except Exception as e:
                logger.warning("Google Places error: %s", e)
    return results


async def _overpass(lat: float, lng: float, level: int, radius: int) -> list[Facility]:
    amenity_map = {
        0: ["pharmacy"],
        1: ["pharmacy"],
        2: ["doctors", "clinic", "health_centre"],
        3: ["hospital", "urgent_care", "doctors"],
        4: ["hospital", "emergency"],
    }
    amenities = "|".join(amenity_map[level])
    query = (
        f'[out:json][timeout:12];'
        f'(node["amenity"~"^({amenities})$"](around:{radius},{lat},{lng});'
        f'way["amenity"~"^({amenities})$"](around:{radius},{lat},{lng}););'
        f'out center 15;'
    )
    results = []
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            r = await client.post(_OVERPASS_URL, data={"data": query})
            data = r.json()
        for el in data.get("elements", []):
            tags = el.get("tags", {})
            elat = el.get("lat") or el.get("center", {}).get("lat")
            elng = el.get("lon") or el.get("center", {}).get("lon")
            if not elat or not elng:
                continue
            dist = _haversine(lat, lng, elat, elng)
            name = tags.get("name") or tags.get("operator") or "Medical Facility"
            addr_parts = [
                tags.get("addr:housenumber", ""),
                tags.get("addr:street", ""),
                tags.get("addr:city", ""),
            ]
            address = " ".join(p for p in addr_parts if p) or "See map for address"
            results.append(Facility(
                name=name,
                address=address,
                phone=tags.get("phone") or tags.get("contact:phone"),
                distance_km=round(dist, 2),
                facility_type=tags.get("amenity", "medical"),
                lat=elat,
                lng=elng,
                maps_url=f"https://www.openstreetmap.org/?mlat={elat}&mlon={elng}&zoom=17",
            ))
    except Exception as e:
        logger.error("Overpass API error: %s", e)
        raise HTTPException(status_code=503, detail="Facility lookup unavailable. Please search manually.")
    return results


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

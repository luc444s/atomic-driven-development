"""Geocoding proxy local (Nominatim vía el backend).

El navegador de la tablet no siempre resuelve el fetch directo a Nominatim;
el backend sí tiene salida a internet. Estos endpoints hacen el search y el
reverse geocoding por el servidor y devuelven el resultado estructurado.
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Any

from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/geocode", tags=["geocode"])

NOMINATIM_BASE = "https://nominatim.openstreetmap.org"
TIMEOUT_SECONDS = 10
HEADERS = {
    "User-Agent": "systutor-oss/1.0 (logistics)",
    "Accept-Language": "es",
    "Accept": "application/json",
}


def _fetch(url: str) -> Any:
    request = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001 - proxy debe degradar a error HTTP
        raise HTTPException(status_code=502, detail=f"geocoder no disponible: {exc}") from exc


@router.get("/reverse")
def reverse_geocode(
    lat: float = Query(...),
    lng: float = Query(...),
) -> dict[str, Any]:
    url = (
        f"{NOMINATIM_BASE}/reverse?format=json&lat={lat}&lon={lng}"
    )
    data = _fetch(url)
    if not isinstance(data, dict) or not data.get("display_name"):
        return {"display_name": None, "address": {}}
    return {
        "display_name": data["display_name"],
        "address": data.get("address") or {},
    }


@router.get("/search")
def search_geocode(
    q: str = Query(..., min_length=2),
    limit: int = Query(default=5, ge=1, le=10),
) -> list[dict[str, Any]]:
    url = f"{NOMINATIM_BASE}/search?format=json&limit={limit}&q={urllib.parse.quote(q)}"
    data = _fetch(url)
    if not isinstance(data, list):
        return []
    return [
        {
            "lat": float(item["lat"]),
            "lng": float(item["lon"]),
            "display_name": item.get("display_name", ""),
        }
        for item in data
        if item.get("lat") and item.get("lon")
    ]

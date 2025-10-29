from __future__ import annotations

from fastapi import APIRouter

from ..constants import DELIVERY_PREFERENCES, PRICING_TIERS
from ..schemas import LookupResponse

router = APIRouter()


@router.get("/targeting", response_model=LookupResponse)
def get_targeting_lookups() -> LookupResponse:
    return LookupResponse()


@router.get("/pricing-tiers")
def get_pricing_tiers() -> dict[str, dict[str, int]]:
    return PRICING_TIERS


@router.get("/delivery-preferences")
def get_delivery_preferences() -> dict[str, list[str]]:
    return {"delivery_preferences": sorted(DELIVERY_PREFERENCES)}

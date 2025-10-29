from __future__ import annotations

ALLOWED_REGIONS = [
    "US",
    "CA",
    "GB",
    "FR",
    "DE",
    "AU",
    "JP",
    "BR",
    "IN",
    "SG",
]

PRICING_TIERS = {
    "starter": {"min_price_cents": 5000, "max_price_cents": 20000},
    "growth": {"min_price_cents": 20001, "max_price_cents": 50000},
    "enterprise": {"min_price_cents": 50001, "max_price_cents": 200000},
}

DELIVERY_PREFERENCES = {"immediate", "scheduled", "batch"}

AGE_RANGE_LOOKUPS = [
    {"label": "18-24", "min": 18, "max": 24},
    {"label": "25-34", "min": 25, "max": 34},
    {"label": "35-44", "min": 35, "max": 44},
    {"label": "45-54", "min": 45, "max": 54},
    {"label": "55-65", "min": 55, "max": 65},
]

MIN_AGE = 18
MAX_AGE = 65

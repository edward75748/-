from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

from .constants import (
    AGE_RANGE_LOOKUPS,
    ALLOWED_REGIONS,
    DELIVERY_PREFERENCES,
    MAX_AGE,
    MIN_AGE,
    PRICING_TIERS,
)


class AdvertiserBase(BaseModel):
    name: str = Field(..., max_length=255)
    status: str = Field("active", max_length=50)


class AdvertiserCreate(AdvertiserBase):
    pass


class AdvertiserUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    status: Optional[str] = Field(default=None, max_length=50)


class AdvertiserOut(AdvertiserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdvertiserAccountBase(BaseModel):
    advertiser_id: int
    name: str = Field(..., max_length=255)
    balance_cents: int = Field(ge=0, default=0)
    currency: str = Field("USD", min_length=3, max_length=3)
    status: str = Field("active", max_length=50)


class AdvertiserAccountCreate(AdvertiserAccountBase):
    pass


class AdvertiserAccountUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    balance_cents: Optional[int] = Field(default=None, ge=0)
    currency: Optional[str] = Field(default=None, min_length=3, max_length=3)
    status: Optional[str] = Field(default=None, max_length=50)


class AdvertiserAccountOut(AdvertiserAccountBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CampaignBase(BaseModel):
    advertiser_account_id: int
    name: str = Field(..., max_length=255)
    pricing_tier: str
    price_cents: int = Field(..., gt=0)
    age_min: int
    age_max: int
    allowed_regions: List[str] = Field(..., min_length=1)
    is_active: bool = True
    daily_cap_cents: Optional[int] = Field(default=None, gt=0)
    total_cap_cents: Optional[int] = Field(default=None, gt=0)
    webhook_url: Optional[HttpUrl] = None
    delivery_preference: str = Field(default="immediate")

    @field_validator("pricing_tier")
    @classmethod
    def validate_pricing_tier(cls, value: str) -> str:
        if value not in PRICING_TIERS:
            raise ValueError("Unknown pricing tier")
        return value

    @field_validator("price_cents")
    @classmethod
    def validate_pricing(cls, value: int, info):
        pricing_tier = info.data.get("pricing_tier")
        if pricing_tier and pricing_tier in PRICING_TIERS:
            tier = PRICING_TIERS[pricing_tier]
            if not (tier["min_price_cents"] <= value <= tier["max_price_cents"]):
                raise ValueError("Price is outside the configured tier bounds")
        return value

    @field_validator("allowed_regions")
    @classmethod
    def validate_regions(cls, value: List[str]) -> List[str]:
        invalid = [region for region in value if region not in ALLOWED_REGIONS]
        if invalid:
            raise ValueError(f"Invalid regions provided: {', '.join(invalid)}")
        return value

    @field_validator("age_min", "age_max")
    @classmethod
    def validate_age_bounds(cls, value: int) -> int:
        if value < MIN_AGE or value > MAX_AGE:
            raise ValueError(
                f"Age values must be within the supported range of {MIN_AGE}-{MAX_AGE}"
            )
        return value

    @field_validator("delivery_preference")
    @classmethod
    def validate_delivery_preference(cls, value: str) -> str:
        if value not in DELIVERY_PREFERENCES:
            raise ValueError("Unsupported delivery preference")
        return value

    @field_validator("total_cap_cents")
    @classmethod
    def validate_total_cap(cls, value: Optional[int]) -> Optional[int]:
        return value

    @field_validator("daily_cap_cents")
    @classmethod
    def validate_caps(
        cls, value: Optional[int], info
    ) -> Optional[int]:  # pylint: disable=unused-argument
        total = info.data.get("total_cap_cents")
        if value and total and value > total:
            raise ValueError("Daily cap cannot exceed the total cap")
        return value

    @field_validator("age_max")
    @classmethod
    def validate_age_order(cls, value: int, info):
        age_min = info.data.get("age_min")
        if age_min and value < age_min:
            raise ValueError("Maximum age must be greater than or equal to minimum age")
        return value


class CampaignCreate(CampaignBase):
    pass


class CampaignUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    pricing_tier: Optional[str] = None
    price_cents: Optional[int] = Field(default=None, gt=0)
    age_min: Optional[int] = None
    age_max: Optional[int] = None
    allowed_regions: Optional[List[str]] = None
    is_active: Optional[bool] = None
    daily_cap_cents: Optional[int] = Field(default=None, gt=0)
    total_cap_cents: Optional[int] = Field(default=None, gt=0)
    webhook_url: Optional[HttpUrl] = None
    delivery_preference: Optional[str] = None

    @field_validator("pricing_tier")
    @classmethod
    def validate_pricing_tier(cls, value: Optional[str]) -> Optional[str]:
        if value and value not in PRICING_TIERS:
            raise ValueError("Unknown pricing tier")
        return value

    @field_validator("allowed_regions")
    @classmethod
    def validate_regions(cls, value: Optional[List[str]]) -> Optional[List[str]]:
        if value is None:
            return value
        invalid = [region for region in value if region not in ALLOWED_REGIONS]
        if invalid:
            raise ValueError(f"Invalid regions provided: {', '.join(invalid)}")
        return value

    @field_validator("daily_cap_cents")
    @classmethod
    def validate_daily_cap(cls, value: Optional[int], info):
        total = info.data.get("total_cap_cents")
        if value and total and value > total:
            raise ValueError("Daily cap cannot exceed the total cap")
        return value

    @field_validator("delivery_preference")
    @classmethod
    def validate_delivery_preference(cls, value: Optional[str]) -> Optional[str]:
        if value and value not in DELIVERY_PREFERENCES:
            raise ValueError("Unsupported delivery preference")
        return value


class AdvertiserAccountSummary(BaseModel):
    id: int
    name: str
    balance_cents: int
    currency: str

    model_config = ConfigDict(from_attributes=True)


class CampaignOut(BaseModel):
    id: int
    name: str
    pricing_tier: str
    price_cents: int
    age_min: int
    age_max: int
    allowed_regions: List[str]
    is_active: bool
    daily_cap_cents: Optional[int]
    total_cap_cents: Optional[int]
    webhook_url: Optional[HttpUrl]
    delivery_preference: str
    advertiser_account_id: int
    account: AdvertiserAccountSummary
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CampaignList(BaseModel):
    items: List[CampaignOut]
    total: int


class AuditLogOut(BaseModel):
    id: int
    entity_type: str
    entity_id: int
    action: str
    before_state: Optional[dict]
    after_state: Optional[dict]
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LookupResponse(BaseModel):
    regions: List[str] = Field(default_factory=lambda: list(ALLOWED_REGIONS))
    age_ranges: List[dict] = Field(default_factory=lambda: list(AGE_RANGE_LOOKUPS))


class UserOut(BaseModel):
    id: int
    email: str
    role: str
    advertiser_id: Optional[int]

    model_config = ConfigDict(from_attributes=True)

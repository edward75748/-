from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, selectinload

from .. import audit
from ..constants import PRICING_TIERS
from ..database import get_db
from ..dependencies import get_current_user
from ..models import AdvertiserAccount, Campaign, User
from ..rbac import ensure_account_access, ensure_campaign_access
from ..schemas import CampaignCreate, CampaignList, CampaignOut, CampaignUpdate

router = APIRouter()


def _validate_pricing(pricing_tier: str, price_cents: int) -> None:
    tier = PRICING_TIERS.get(pricing_tier)
    if not tier:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unknown pricing tier")
    if not (tier["min_price_cents"] <= price_cents <= tier["max_price_cents"]):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Price is outside the configured tier bounds",
        )


def _validate_caps(daily_cap: Optional[int], total_cap: Optional[int]) -> None:
    if daily_cap and total_cap and daily_cap > total_cap:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Daily cap cannot exceed total cap",
        )


def _validate_age(age_min: int, age_max: int) -> None:
    if age_min > age_max:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Maximum age must be greater than or equal to minimum age",
        )


def _deduplicate_regions(regions: list[str]) -> list[str]:
    seen = set()
    deduped = []
    for region in regions:
        if region not in seen:
            deduped.append(region)
            seen.add(region)
    return deduped


@router.post("/", response_model=CampaignOut, status_code=status.HTTP_201_CREATED)
def create_campaign(
    payload: CampaignCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account = (
        db.query(AdvertiserAccount)
        .options(selectinload(AdvertiserAccount.advertiser))
        .filter(AdvertiserAccount.id == payload.advertiser_account_id)
        .first()
    )
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    ensure_account_access(current_user, account)

    _validate_pricing(payload.pricing_tier, payload.price_cents)
    _validate_caps(payload.daily_cap_cents, payload.total_cap_cents)
    _validate_age(payload.age_min, payload.age_max)

    campaign = Campaign(
        advertiser_account_id=payload.advertiser_account_id,
        name=payload.name,
        pricing_tier=payload.pricing_tier,
        price_cents=payload.price_cents,
        age_min=payload.age_min,
        age_max=payload.age_max,
        allowed_regions=_deduplicate_regions(payload.allowed_regions),
        is_active=payload.is_active,
        daily_cap_cents=payload.daily_cap_cents,
        total_cap_cents=payload.total_cap_cents,
        webhook_url=payload.webhook_url,
        delivery_preference=payload.delivery_preference,
    )
    db.add(campaign)
    db.flush()
    audit.log_action(
        db,
        user_id=current_user.id,
        entity_type="campaign",
        entity_id=campaign.id,
        action="create",
        before_state=None,
        after_state=audit.serialize_instance(campaign),
    )
    db.commit()
    db.refresh(campaign)
    return campaign


@router.get("/", response_model=CampaignList)
def list_campaigns(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, gt=0, le=200),
    advertiser_account_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Campaign).options(selectinload(Campaign.account))
    if advertiser_account_id is not None:
        query = query.filter(Campaign.advertiser_account_id == advertiser_account_id)
    if current_user.role == "advertiser_user":
        query = query.join(Campaign.account).filter(
            AdvertiserAccount.advertiser_id == current_user.advertiser_id
        )
    total = query.count()
    campaigns = query.offset(skip).limit(limit).all()
    return {"items": campaigns, "total": total}


@router.get("/{campaign_id}", response_model=CampaignOut)
def get_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    campaign = (
        db.query(Campaign)
        .options(selectinload(Campaign.account))
        .filter(Campaign.id == campaign_id)
        .first()
    )
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    ensure_campaign_access(current_user, campaign)
    return campaign


@router.put("/{campaign_id}", response_model=CampaignOut)
def update_campaign(
    campaign_id: int,
    payload: CampaignUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    campaign = (
        db.query(Campaign)
        .options(selectinload(Campaign.account))
        .filter(Campaign.id == campaign_id)
        .first()
    )
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    ensure_campaign_access(current_user, campaign)

    update_data = payload.model_dump(exclude_unset=True)
    if "allowed_regions" in update_data and update_data["allowed_regions"] is not None:
        update_data["allowed_regions"] = _deduplicate_regions(update_data["allowed_regions"])

    pricing_tier = update_data.get("pricing_tier", campaign.pricing_tier)
    price_cents = update_data.get("price_cents", campaign.price_cents)
    _validate_pricing(pricing_tier, price_cents)

    age_min = update_data.get("age_min", campaign.age_min)
    age_max = update_data.get("age_max", campaign.age_max)
    _validate_age(age_min, age_max)

    daily_cap = update_data.get("daily_cap_cents", campaign.daily_cap_cents)
    total_cap = update_data.get("total_cap_cents", campaign.total_cap_cents)
    _validate_caps(daily_cap, total_cap)

    before = audit.serialize_instance(campaign)
    for field, value in update_data.items():
        setattr(campaign, field, value)
    db.flush()
    audit.log_action(
        db,
        user_id=current_user.id,
        entity_type="campaign",
        entity_id=campaign.id,
        action="update",
        before_state=before,
        after_state=audit.serialize_instance(campaign),
    )
    db.commit()
    db.refresh(campaign)
    return campaign


@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    campaign = (
        db.query(Campaign)
        .options(selectinload(Campaign.account))
        .filter(Campaign.id == campaign_id)
        .first()
    )
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    ensure_campaign_access(current_user, campaign)
    before = audit.serialize_instance(campaign)
    db.delete(campaign)
    audit.log_action(
        db,
        user_id=current_user.id,
        entity_type="campaign",
        entity_id=campaign.id,
        action="delete",
        before_state=before,
        after_state=None,
    )
    db.commit()

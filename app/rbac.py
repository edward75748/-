from __future__ import annotations

from fastapi import HTTPException, status

from .models import AdvertiserAccount, Campaign, User

ADMIN_ROLES = {"admin", "senior_admin"}


def require_admin(user: User) -> None:
    if user.role not in ADMIN_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")


def ensure_account_access(user: User, account: AdvertiserAccount) -> None:
    if user.role in ADMIN_ROLES:
        return
    if user.role == "advertiser_user" and account.advertiser_id == user.advertiser_id:
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")


def ensure_campaign_access(user: User, campaign: Campaign) -> None:
    if user.role in ADMIN_ROLES:
        return
    if user.role == "advertiser_user" and campaign.account.advertiser_id == user.advertiser_id:
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

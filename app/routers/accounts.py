from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import audit
from ..database import get_db
from ..dependencies import get_current_user
from ..models import Advertiser, AdvertiserAccount, User
from ..rbac import ensure_account_access, require_admin
from ..schemas import (
    AdvertiserAccountCreate,
    AdvertiserAccountOut,
    AdvertiserAccountUpdate,
)

router = APIRouter()


@router.post("/", response_model=AdvertiserAccountOut, status_code=status.HTTP_201_CREATED)
def create_account(
    payload: AdvertiserAccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)
    advertiser = db.query(Advertiser).filter(Advertiser.id == payload.advertiser_id).first()
    if not advertiser:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Advertiser not found")
    account = AdvertiserAccount(**payload.model_dump())
    db.add(account)
    db.flush()
    audit.log_action(
        db,
        user_id=current_user.id,
        entity_type="account",
        entity_id=account.id,
        action="create",
        before_state=None,
        after_state=audit.serialize_instance(account),
    )
    db.commit()
    db.refresh(account)
    return account


@router.get("/", response_model=List[AdvertiserAccountOut])
def list_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(AdvertiserAccount)
    if current_user.role == "advertiser_user":
        if current_user.advertiser_id is None:
            return []
        query = query.filter(AdvertiserAccount.advertiser_id == current_user.advertiser_id)
    accounts = query.order_by(AdvertiserAccount.name.asc()).all()
    return accounts


@router.get("/{account_id}", response_model=AdvertiserAccountOut)
def get_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account = db.query(AdvertiserAccount).filter(AdvertiserAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    ensure_account_access(current_user, account)
    return account


@router.put("/{account_id}", response_model=AdvertiserAccountOut)
def update_account(
    account_id: int,
    payload: AdvertiserAccountUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)
    account = db.query(AdvertiserAccount).filter(AdvertiserAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    before = audit.serialize_instance(account)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(account, field, value)
    db.flush()
    audit.log_action(
        db,
        user_id=current_user.id,
        entity_type="account",
        entity_id=account.id,
        action="update",
        before_state=before,
        after_state=audit.serialize_instance(account),
    )
    db.commit()
    db.refresh(account)
    return account


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)
    account = db.query(AdvertiserAccount).filter(AdvertiserAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    before = audit.serialize_instance(account)
    db.delete(account)
    audit.log_action(
        db,
        user_id=current_user.id,
        entity_type="account",
        entity_id=account.id,
        action="delete",
        before_state=before,
        after_state=None,
    )
    db.commit()

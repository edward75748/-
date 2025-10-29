from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import audit
from ..dependencies import get_current_user
from ..models import Advertiser, User
from ..rbac import require_admin
from ..schemas import AdvertiserCreate, AdvertiserOut, AdvertiserUpdate
from ..database import get_db

router = APIRouter()


@router.post("/", response_model=AdvertiserOut, status_code=status.HTTP_201_CREATED)
def create_advertiser(
    payload: AdvertiserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)
    advertiser = Advertiser(**payload.model_dump())
    db.add(advertiser)
    db.flush()
    audit.log_action(
        db,
        user_id=current_user.id,
        entity_type="advertiser",
        entity_id=advertiser.id,
        action="create",
        before_state=None,
        after_state=audit.serialize_instance(advertiser),
    )
    db.commit()
    db.refresh(advertiser)
    return advertiser


@router.get("/", response_model=List[AdvertiserOut])
def list_advertisers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Advertiser)
    if current_user.role == "advertiser_user":
        if current_user.advertiser_id is None:
            return []
        query = query.filter(Advertiser.id == current_user.advertiser_id)
    advertisers = query.order_by(Advertiser.name.asc()).all()
    return advertisers


@router.get("/{advertiser_id}", response_model=AdvertiserOut)
def get_advertiser(
    advertiser_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    advertiser = db.query(Advertiser).filter(Advertiser.id == advertiser_id).first()
    if not advertiser:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Advertiser not found")

    if current_user.role == "advertiser_user" and current_user.advertiser_id != advertiser.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    return advertiser


@router.put("/{advertiser_id}", response_model=AdvertiserOut)
def update_advertiser(
    advertiser_id: int,
    payload: AdvertiserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)
    advertiser = db.query(Advertiser).filter(Advertiser.id == advertiser_id).first()
    if not advertiser:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Advertiser not found")
    before = audit.serialize_instance(advertiser)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(advertiser, field, value)
    db.flush()
    audit.log_action(
        db,
        user_id=current_user.id,
        entity_type="advertiser",
        entity_id=advertiser.id,
        action="update",
        before_state=before,
        after_state=audit.serialize_instance(advertiser),
    )
    db.commit()
    db.refresh(advertiser)
    return advertiser


@router.delete("/{advertiser_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_advertiser(
    advertiser_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)
    advertiser = db.query(Advertiser).filter(Advertiser.id == advertiser_id).first()
    if not advertiser:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Advertiser not found")
    before = audit.serialize_instance(advertiser)
    db.delete(advertiser)
    audit.log_action(
        db,
        user_id=current_user.id,
        entity_type="advertiser",
        entity_id=advertiser.id,
        action="delete",
        before_state=before,
        after_state=None,
    )
    db.commit()

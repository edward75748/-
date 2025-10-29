from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from .database import Base


class TimestampMixin:
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class Advertiser(Base, TimestampMixin):
    __tablename__ = "advertisers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    status = Column(String(50), nullable=False, default="active")

    accounts = relationship("AdvertiserAccount", back_populates="advertiser", cascade="all,delete")


class AdvertiserAccount(Base, TimestampMixin):
    __tablename__ = "advertiser_accounts"

    id = Column(Integer, primary_key=True, index=True)
    advertiser_id = Column(Integer, ForeignKey("advertisers.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    balance_cents = Column(Integer, nullable=False, default=0)
    currency = Column(String(3), nullable=False, default="USD")
    status = Column(String(50), nullable=False, default="active")

    advertiser = relationship("Advertiser", back_populates="accounts")
    campaigns = relationship("Campaign", back_populates="account", cascade="all,delete")


class Campaign(Base, TimestampMixin):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    advertiser_account_id = Column(
        Integer, ForeignKey("advertiser_accounts.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String(255), nullable=False)
    pricing_tier = Column(String(50), nullable=False)
    price_cents = Column(Integer, nullable=False)
    age_min = Column(Integer, nullable=False)
    age_max = Column(Integer, nullable=False)
    allowed_regions = Column(JSON, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    daily_cap_cents = Column(Integer, nullable=True)
    total_cap_cents = Column(Integer, nullable=True)
    webhook_url = Column(String(500), nullable=True)
    delivery_preference = Column(String(50), nullable=False, default="immediate")

    account = relationship("AdvertiserAccount", back_populates="campaigns")


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, unique=True)
    role = Column(String(50), nullable=False)
    advertiser_id = Column(Integer, ForeignKey("advertisers.id"), nullable=True)

    advertiser = relationship("Advertiser")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(Integer, nullable=False)
    action = Column(String(50), nullable=False)
    before_state = Column(JSON, nullable=True)
    after_state = Column(JSON, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    user = relationship("User")

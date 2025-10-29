from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import AuditLog, Campaign


def test_campaign_flow(
    client: TestClient,
    db_session: Session,
    admin_user,
    advertiser_user_factory,
):
    advertiser_response = client.post(
        "/advertisers/",
        json={"name": "Acme Corp", "status": "active"},
        headers={"X-User-Id": str(admin_user.id)},
    )
    assert advertiser_response.status_code == 201
    advertiser_id = advertiser_response.json()["id"]

    advertiser_user = advertiser_user_factory(advertiser_id, email="owner@acme.test")

    account_response = client.post(
        "/accounts/",
        json={
            "advertiser_id": advertiser_id,
            "name": "Primary Account",
            "balance_cents": 450000,
            "currency": "USD",
            "status": "active",
        },
        headers={"X-User-Id": str(admin_user.id)},
    )
    assert account_response.status_code == 201
    account_payload = account_response.json()
    account_id = account_payload["id"]
    assert account_payload["balance_cents"] == 450000

    campaign_response = client.post(
        "/campaigns/",
        json={
            "advertiser_account_id": account_id,
            "name": "Spring Launch",
            "pricing_tier": "starter",
            "price_cents": 7500,
            "age_min": 25,
            "age_max": 44,
            "allowed_regions": ["US", "CA", "US"],
            "is_active": True,
            "daily_cap_cents": 15000,
            "total_cap_cents": 60000,
            "webhook_url": "https://hooks.acme.test/deliveries",
            "delivery_preference": "scheduled",
        },
        headers={"X-User-Id": str(advertiser_user.id)},
    )
    assert campaign_response.status_code == 201
    body = campaign_response.json()
    assert body["advertiser_account_id"] == account_id
    assert body["allowed_regions"] == ["US", "CA"]  # duplicates removed
    assert body["account"]["balance_cents"] == 450000
    assert body["delivery_preference"] == "scheduled"

    update_response = client.put(
        f"/campaigns/{body['id']}",
        json={
            "is_active": False,
            "price_cents": 6000,
            "daily_cap_cents": 12000,
        },
        headers={"X-User-Id": str(advertiser_user.id)},
    )
    assert update_response.status_code == 200
    updated_campaign = update_response.json()
    assert updated_campaign["is_active"] is False
    assert updated_campaign["price_cents"] == 6000
    assert updated_campaign["daily_cap_cents"] == 12000

    list_response = client.get(
        "/campaigns/",
        headers={"X-User-Id": str(advertiser_user.id)},
    )
    assert list_response.status_code == 200
    listing = list_response.json()
    assert listing["total"] == 1
    assert listing["items"][0]["id"] == body["id"]


def test_pricing_and_region_validation(
    client: TestClient,
    admin_user,
    advertiser_user_factory,
):
    advertiser_response = client.post(
        "/advertisers/",
        json={"name": "Validation Inc", "status": "active"},
        headers={"X-User-Id": str(admin_user.id)},
    )
    advertiser_id = advertiser_response.json()["id"]
    advertiser_user = advertiser_user_factory(advertiser_id, email="user@validation.test")
    account_response = client.post(
        "/accounts/",
        json={"advertiser_id": advertiser_id, "name": "Validation", "balance_cents": 100000},
        headers={"X-User-Id": str(admin_user.id)},
    )
    account_id = account_response.json()["id"]

    invalid_pricing = client.post(
        "/campaigns/",
        json={
            "advertiser_account_id": account_id,
            "name": "Invalid Pricing",
            "pricing_tier": "starter",
            "price_cents": 100,
            "age_min": 25,
            "age_max": 30,
            "allowed_regions": ["US"],
            "is_active": True,
        },
        headers={"X-User-Id": str(advertiser_user.id)},
    )
    assert invalid_pricing.status_code == 422

    invalid_regions = client.post(
        "/campaigns/",
        json={
            "advertiser_account_id": account_id,
            "name": "Invalid Regions",
            "pricing_tier": "starter",
            "price_cents": 7000,
            "age_min": 25,
            "age_max": 30,
            "allowed_regions": ["US", "XX"],
            "is_active": True,
        },
        headers={"X-User-Id": str(advertiser_user.id)},
    )
    assert invalid_regions.status_code == 422

    invalid_caps = client.post(
        "/campaigns/",
        json={
            "advertiser_account_id": account_id,
            "name": "Invalid Caps",
            "pricing_tier": "starter",
            "price_cents": 8000,
            "age_min": 25,
            "age_max": 30,
            "allowed_regions": ["US"],
            "is_active": True,
            "daily_cap_cents": 50000,
            "total_cap_cents": 1000,
        },
        headers={"X-User-Id": str(advertiser_user.id)},
    )
    assert invalid_caps.status_code == 422


def test_rbac_prevents_cross_account_updates(
    client: TestClient,
    db_session: Session,
    admin_user,
    advertiser_user_factory,
):
    # Setup two advertisers and accounts
    adv1 = client.post(
        "/advertisers/",
        json={"name": "First Advertiser", "status": "active"},
        headers={"X-User-Id": str(admin_user.id)},
    ).json()
    adv2 = client.post(
        "/advertisers/",
        json={"name": "Second Advertiser", "status": "active"},
        headers={"X-User-Id": str(admin_user.id)},
    ).json()
    account1 = client.post(
        "/accounts/",
        json={"advertiser_id": adv1["id"], "name": "Account 1", "balance_cents": 200000},
        headers={"X-User-Id": str(admin_user.id)},
    ).json()
    account2 = client.post(
        "/accounts/",
        json={"advertiser_id": adv2["id"], "name": "Account 2", "balance_cents": 200000},
        headers={"X-User-Id": str(admin_user.id)},
    ).json()

    user1 = advertiser_user_factory(adv1["id"], email="owner1@test.com")
    user2 = advertiser_user_factory(adv2["id"], email="owner2@test.com")

    campaign = client.post(
        "/campaigns/",
        json={
            "advertiser_account_id": account1["id"],
            "name": "Protected",
            "pricing_tier": "starter",
            "price_cents": 9000,
            "age_min": 25,
            "age_max": 50,
            "allowed_regions": ["US"],
            "is_active": True,
        },
        headers={"X-User-Id": str(user1.id)},
    ).json()

    unauthorized_update = client.put(
        f"/campaigns/{campaign['id']}",
        json={"name": "Hacked"},
        headers={"X-User-Id": str(user2.id)},
    )
    assert unauthorized_update.status_code == 403

    # Admin can update
    admin_update = client.put(
        f"/campaigns/{campaign['id']}",
        json={"name": "Legit Update", "price_cents": 9500},
        headers={"X-User-Id": str(admin_user.id)},
    )
    assert admin_update.status_code == 200
    assert admin_update.json()["name"] == "Legit Update"


def test_audit_log_records_changes(
    client: TestClient,
    db_session: Session,
    admin_user,
    advertiser_user_factory,
):
    advertiser = client.post(
        "/advertisers/",
        json={"name": "Audit Co", "status": "active"},
        headers={"X-User-Id": str(admin_user.id)},
    ).json()
    advertiser_user = advertiser_user_factory(advertiser["id"], email="audit@co.test")
    account = client.post(
        "/accounts/",
        json={"advertiser_id": advertiser["id"], "name": "Audit Account", "balance_cents": 50000},
        headers={"X-User-Id": str(admin_user.id)},
    ).json()
    campaign = client.post(
        "/campaigns/",
        json={
            "advertiser_account_id": account["id"],
            "name": "Trackable",
            "pricing_tier": "starter",
            "price_cents": 5500,
            "age_min": 25,
            "age_max": 35,
            "allowed_regions": ["US"],
            "is_active": True,
        },
        headers={"X-User-Id": str(advertiser_user.id)},
    ).json()

    update_response = client.put(
        f"/campaigns/{campaign['id']}",
        json={"is_active": False, "price_cents": 5800},
        headers={"X-User-Id": str(advertiser_user.id)},
    )
    assert update_response.status_code == 200

    audit_logs = (
        db_session.query(AuditLog)
        .filter(AuditLog.entity_type == "campaign", AuditLog.entity_id == campaign["id"])
        .order_by(AuditLog.id.asc())
        .all()
    )
    assert len(audit_logs) >= 2  # create and update
    last_log = audit_logs[-1]
    assert last_log.action == "update"
    assert last_log.before_state["is_active"] is True
    assert last_log.after_state["is_active"] is False
    assert last_log.after_state["price_cents"] == 5800

    # Ensure campaign data persisted
    refreshed = db_session.get(Campaign, campaign["id"])
    assert refreshed is not None
    assert refreshed.is_active is False
    assert refreshed.price_cents == 5800

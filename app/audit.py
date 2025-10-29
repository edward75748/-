from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from .models import AuditLog, Base


def serialize_instance(instance: Base, exclude: Optional[Iterable[str]] = None) -> Dict[str, Any]:
    exclude = set(exclude or [])
    data: Dict[str, Any] = {}
    for column in instance.__table__.columns:  # type: ignore[attr-defined]
        name = column.name
        if name in exclude:
            continue
        data[name] = getattr(instance, name)
    return jsonable_encoder(data)


def log_action(
    db: Session,
    *,
    user_id: int,
    entity_type: str,
    entity_id: int,
    action: str,
    before_state: Optional[Dict[str, Any]] = None,
    after_state: Optional[Dict[str, Any]] = None,
) -> AuditLog:
    audit_log = AuditLog(
        user_id=user_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        before_state=before_state,
        after_state=after_state,
    )
    db.add(audit_log)
    return audit_log

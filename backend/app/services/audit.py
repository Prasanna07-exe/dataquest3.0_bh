from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.audit import AuditLog


def record_audit(
    db: Session,
    service_request_id: int,
    action: str,
    actor_user_id: int | None = None,
    from_state: str | None = None,
    to_state: str | None = None,
    details: str | None = None,
) -> AuditLog:
    audit = AuditLog(
        service_request_id=service_request_id,
        actor_user_id=actor_user_id,
        action=action,
        from_state=from_state,
        to_state=to_state,
        details=details,
        created_at=datetime.now(timezone.utc),
    )

    db.add(audit)
    db.flush()

    return audit
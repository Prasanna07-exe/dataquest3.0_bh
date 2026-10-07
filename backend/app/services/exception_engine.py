from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.models.exception_event import ExceptionEvent


def create_exception(
    db: Session,
    service_request_id: int,
    exception_type: str,
    severity: str,
    description: str,
    recommended_action: str | None = None,
) -> ExceptionEvent:
    exception_event = ExceptionEvent(
        service_request_id=service_request_id,
        exception_type=exception_type,
        severity=severity,
        status="OPEN",
        description=description,
        recommended_action=recommended_action,
    )

    db.add(exception_event)
    db.flush()

    return exception_event

def detect_technician_dropout(
    db: Session,
    service_request_id: int,
    technician_id: int,
):
    return create_exception(
        db=db,
        service_request_id=service_request_id,
        exception_type="TECHNICIAN_DROPOUT",
        severity="HIGH",
        description=f"Technician {technician_id} is no longer available for the assigned service request.",
        recommended_action="Find and assign the highest-ranked feasible replacement technician.",
    )

def resolve_exception(
    db: Session,
    exception_id: int,
    recommended_action: str | None = None,
):
    exception_event = (
        db.query(ExceptionEvent)
        .filter(ExceptionEvent.id == exception_id)
        .first()
    )

    if not exception_event:
        return None

    exception_event.status = "RESOLVED"
    exception_event.resolved_at = datetime.now(timezone.utc)

    if recommended_action:
        exception_event.recommended_action = recommended_action

    db.flush()

    return exception_event
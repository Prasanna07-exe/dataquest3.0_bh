from sqlalchemy.orm import Session

from app.models.service_request import ServiceRequest
from app.rules.state_machine import ServiceRequestState, validate_transition
from app.services.audit import record_audit


def transition_service_request(
    db: Session,
    service_request: ServiceRequest,
    new_state: ServiceRequestState,
    action: str,
    actor_user_id: int | None = None,
    details: str | None = None,
) -> None:
    current_state = ServiceRequestState(service_request.state)

    validate_transition(
        current_state,
        new_state,
    )

    service_request.state = new_state.value

    record_audit(
        db=db,
        service_request_id=service_request.id,
        actor_user_id=actor_user_id,
        action=action,
        from_state=current_state.value,
        to_state=new_state.value,
        details=details,
    )
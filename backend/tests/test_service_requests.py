from app.core.database import SessionLocal
from app.models.audit import AuditLog
from app.models.service_request import ServiceRequest
from app.services.state_transition import transition_service_request
import uuid

from app.rules.state_machine import (
    ServiceRequestState,
    can_transition,
    validate_transition,
)


def test_valid_state_transition():
    assert can_transition(
        ServiceRequestState.DRAFT,
        ServiceRequestState.SUBMITTED,
    )


def test_invalid_state_transition():
    assert not can_transition(
        ServiceRequestState.DRAFT,
        ServiceRequestState.CLOSED,
    )


def test_validate_transition_accepts_valid_transition():
    validate_transition(
        ServiceRequestState.SUBMITTED,
        ServiceRequestState.VALIDATING,
    )


def test_validate_transition_rejects_invalid_transition():
    try:
        validate_transition(
            ServiceRequestState.DRAFT,
            ServiceRequestState.CLOSED,
        )
        assert False, "Expected invalid transition to raise ValueError"
    except ValueError:
        assert True

def test_transition_service_request_records_audit():
    db = SessionLocal()

    request = ServiceRequest(
        request_code=f"TEST-AUDIT-{uuid.uuid4().hex[:8].upper()}",
        state=ServiceRequestState.DRAFT.value,
        customer_id=1,
        site_id=1,
        machine_id=1,
        created_by=1,
        title="Audit unit test",
        description="Testing audit transition",
        maintenance_mode="REACTIVE",
    )

    db.add(request)
    db.flush()

    transition_service_request(
        db=db,
        service_request=request,
        new_state=ServiceRequestState.SUBMITTED,
        action="TEST_SUBMIT",
        actor_user_id=1,
        details="Unit test transition.",
    )

    db.commit()

    audit = (
        db.query(AuditLog)
        .filter(AuditLog.service_request_id == request.id)
        .first()
    )

    assert request.state == ServiceRequestState.SUBMITTED.value
    assert audit is not None
    assert audit.actor_user_id == 1
    assert audit.action == "TEST_SUBMIT"
    assert audit.from_state == ServiceRequestState.DRAFT.value
    assert audit.to_state == ServiceRequestState.SUBMITTED.value
    db.query(AuditLog).filter(
        AuditLog.service_request_id == request.id
    ).delete(synchronize_session=False)
    db.delete(request)
    db.commit()
    db.close()
from app.core.constants import ServiceRequestState


ALLOWED_TRANSITIONS: dict[ServiceRequestState, set[ServiceRequestState]] = {
    ServiceRequestState.DRAFT: {
        ServiceRequestState.SUBMITTED,
    },
    ServiceRequestState.SUBMITTED: {
        ServiceRequestState.CLASSIFYING,
        ServiceRequestState.VALIDATING,
    },
    ServiceRequestState.CLASSIFYING: {
        ServiceRequestState.VALIDATING,
        ServiceRequestState.NEEDS_REVIEW,
    },
    ServiceRequestState.VALIDATING: {
        ServiceRequestState.VALIDATED,
        ServiceRequestState.NEEDS_REVIEW,
    },
    ServiceRequestState.NEEDS_REVIEW: {
        ServiceRequestState.VALIDATING,
        ServiceRequestState.REJECTED,
    },
    ServiceRequestState.VALIDATED: {
        ServiceRequestState.PLANNING,
    },
    ServiceRequestState.PLANNING: {
        ServiceRequestState.RESOURCE_CHECK,
    },
    ServiceRequestState.RESOURCE_CHECK: {
        ServiceRequestState.RESOURCES_READY,
        ServiceRequestState.BLOCKED_BY_RESOURCE,
    },
    ServiceRequestState.BLOCKED_BY_RESOURCE: {
        ServiceRequestState.RESOLVING,
    },
    ServiceRequestState.RESOLVING: {
        ServiceRequestState.RESOURCE_CHECK,
        ServiceRequestState.REJECTED,
    },
    ServiceRequestState.RESOURCES_READY: {
        ServiceRequestState.PENDING_APPROVAL,
    },
    ServiceRequestState.PENDING_APPROVAL: {
        ServiceRequestState.APPROVED,
        ServiceRequestState.REJECTED,
    },
    ServiceRequestState.APPROVED: {
        ServiceRequestState.DISPATCHED,
    },
    ServiceRequestState.DISPATCHED: {
        ServiceRequestState.ACCEPTED_BY_TECH,
        ServiceRequestState.EXCEPTION,
    },
    ServiceRequestState.ACCEPTED_BY_TECH: {
        ServiceRequestState.IN_PROGRESS,
        ServiceRequestState.EXCEPTION,
    },
    ServiceRequestState.IN_PROGRESS: {
        ServiceRequestState.COMPLETED_PENDING_VERIFICATION,
        ServiceRequestState.EXCEPTION,
    },
    ServiceRequestState.EXCEPTION: {
        ServiceRequestState.REASSIGNMENT_PLANNING,
        ServiceRequestState.RESOLVING,
        ServiceRequestState.IN_PROGRESS,
    },
    ServiceRequestState.REASSIGNMENT_PLANNING: {
        ServiceRequestState.DISPATCHED,
        ServiceRequestState.RESOLVING,
        ServiceRequestState.EXCEPTION,
    },
    ServiceRequestState.COMPLETED_PENDING_VERIFICATION: {
        ServiceRequestState.VERIFICATION,
    },
    ServiceRequestState.VERIFICATION: {
        ServiceRequestState.PASSED,
        ServiceRequestState.FAILED,
    },
    ServiceRequestState.FAILED: {
        ServiceRequestState.IN_PROGRESS,
        ServiceRequestState.VERIFICATION,
    },
    ServiceRequestState.PASSED: {
        ServiceRequestState.CUSTOMER_APPROVAL,
    },
    ServiceRequestState.CUSTOMER_APPROVAL: {
        ServiceRequestState.CLOSED,
        ServiceRequestState.IN_PROGRESS,
    },
}


def can_transition(
    current_state: ServiceRequestState,
    new_state: ServiceRequestState,
) -> bool:
    return new_state in ALLOWED_TRANSITIONS.get(current_state, set())


def validate_transition(
    current_state: ServiceRequestState,
    new_state: ServiceRequestState,
) -> None:
    if not can_transition(current_state, new_state):
        raise ValueError(
            f"Invalid service request transition: "
            f"{current_state.value} -> {new_state.value}"
        )
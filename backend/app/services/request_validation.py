from dataclasses import dataclass
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.customer import Customer, Machine, Site
from app.models.service_request import ServiceRequest


@dataclass
class ValidationResult:
    valid: bool
    issues: list[str]


def validate_service_request(
    db: Session,
    request: ServiceRequest,
) -> ValidationResult:
    issues: list[str] = []

    customer = db.get(Customer, request.customer_id)
    site = db.get(Site, request.site_id)
    machine = db.get(Machine, request.machine_id)

    if customer is None:
        issues.append("Customer does not exist.")
    elif not customer.is_active:
        issues.append("Customer is inactive.")

    if site is None:
        issues.append("Site does not exist.")
    elif not site.is_active:
        issues.append("Site is inactive.")

    if machine is None:
        issues.append("Machine does not exist.")
    elif not machine.is_active:
        issues.append("Machine is inactive.")

    if customer and site and site.customer_id != customer.id:
        issues.append("Site does not belong to the selected customer.")

    if site and machine and machine.site_id != site.id:
        issues.append("Machine does not belong to the selected site.")

    if not request.title.strip():
        issues.append("Request title is required.")

    if not request.description.strip():
        issues.append("Request description is required.")

    if not request.maintenance_mode:
        issues.append("Maintenance mode is required.")

    if not request.priority:
        issues.append("Priority is required.")
    existing_request = db.scalar(
        select(ServiceRequest)
        .where(
            ServiceRequest.machine_id == request.machine_id,
            ServiceRequest.id != request.id,
            ServiceRequest.state.notin_(
                ["CLOSED", "REJECTED", "FAILED"]
            ),
        )
        .limit(1)
    )

    if existing_request:
        issues.append(
            f"An active request already exists for this machine: "
            f"{existing_request.request_code}"
        )
    return ValidationResult(
        valid=len(issues) == 0,
        issues=issues,
    )
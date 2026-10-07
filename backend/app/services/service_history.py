from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.service_history import ServiceHistory
from app.models.service_request import RequestAIAnalysis, ServiceRequest
from app.models.assignment import Assignment
from app.models.work_log import WorkLog


def create_service_history(
    db: Session,
    service_request_id: int,
) -> ServiceHistory:
    request = (
        db.query(ServiceRequest)
        .filter(ServiceRequest.id == service_request_id)
        .first()
    )

    if request is None:
        raise ValueError("Service request not found.")

    assignment = (
        db.query(Assignment)
        .filter(
            Assignment.service_request_id == request.id,
            Assignment.status == "COMPLETED",
        )
        .order_by(Assignment.id.desc())
        .first()
    )

    analysis = (
        db.query(RequestAIAnalysis)
        .filter(RequestAIAnalysis.request_id == request.id)
        .order_by(RequestAIAnalysis.id.desc())
        .first()
    )

    work_logs = (
        db.query(WorkLog)
        .filter(WorkLog.service_request_id == request.id)
        .order_by(WorkLog.id)
        .all()
    )

    resolution_summary = "Service completed successfully."

    if work_logs:
        log_summary = "; ".join(
            f"{log.log_type}: {log.description}"
            for log in work_logs
        )
        resolution_summary = log_summary

    existing = (
        db.query(ServiceHistory)
        .filter(ServiceHistory.service_request_id == request.id)
        .first()
    )

    if existing:
        return existing

    history = ServiceHistory(
        machine_id=request.machine_id,
        service_request_id=request.id,
        request_code=request.request_code,
        maintenance_mode=request.maintenance_mode,
        priority=request.priority,
        issue_type=analysis.issue_type if analysis else None,
        failure_mode=analysis.failure_mode if analysis else None,
        resolution_summary=resolution_summary,
        technician_id=assignment.technician_id if assignment else None,
        completed_at=(
            assignment.completed_at
            if assignment and assignment.completed_at
            else datetime.now(timezone.utc)
        ),
    )

    db.add(history)
    db.flush()

    return history
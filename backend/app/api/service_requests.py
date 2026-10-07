from fastapi import APIRouter,File, UploadFile
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from uuid import uuid4
from pathlib import Path
from fastapi.responses import FileResponse
from fastapi import Depends, HTTPException
from app.core.database import get_db
from app.models.service_request import ServiceRequest, RequestAIAnalysis
from app.schemas.service_request import ServiceRequestCreate
from app.rules.state_machine import validate_transition
from app.services.request_validation import validate_service_request
from app.services.sla import calculate_sla
from app.models.technician import Technician, TechnicianAvailability
from app.services.matching import MatchingFactors, rank_technicians
from app.services.resource_check import check_resource_readiness
from app.core.constants import ServiceRequestState
from app.services.orchestration import plan_resources
from app.models.approval import Approval
from app.models.assignment import Assignment
from app.models.work_log import WorkLog
from app.schemas.work_log import WorkLogCreate
from app.services.checklist import create_work_checklist
from app.models.customer import Machine
from app.models.checklist import ChecklistItem, WorkChecklist
from app.schemas.checklist import ChecklistComplete
from app.services.exception_engine import detect_technician_dropout
from app.agents.request_classifier import classify_request
from app.services.service_history import create_service_history
from app.services.attachments import save_attachment
from app.models.attachment import Attachment
from app.schemas.service_request import PartUsageCreate
from app.services.inventory import (
    check_part_availability,
    reserve_part,
    consume_reserved_part,
)
router = APIRouter(prefix="/service-requests", tags=["Service Requests"])


@router.post("")
def create_service_request(
    request: ServiceRequestCreate,
    db: Session = Depends(get_db),
):
    service_request = ServiceRequest(
        request_code=f"SR-{uuid4().hex[:8].upper()}",
        customer_id=request.customer_id,
        site_id=request.site_id,
        machine_id=request.machine_id,
        title=request.title,
        description=request.description,
        maintenance_mode=request.maintenance_mode,
        priority=request.priority,
        state="DRAFT",
        requested_start_at=request.requested_start_at,
        requested_end_at=request.requested_end_at,
        created_by=1,
    )

    db.add(service_request)
    db.commit()
    db.refresh(service_request)

    return service_request

@router.post("/{request_id}/submit")
def submit_service_request(
    request_id: int,
    db: Session = Depends(get_db),
):
    service_request = db.get(ServiceRequest, request_id)

    if service_request is None:
        raise HTTPException(
            status_code=404,
            detail="Service request not found.",
        )

    validate_transition(
        service_request.state,
        "SUBMITTED",
    )

    service_request.state = "SUBMITTED"
    db.commit()
    db.refresh(service_request)

    return service_request

@router.post("/{request_id}/validate")
def validate_request(
    request_id: int,
    db: Session = Depends(get_db),
):
    service_request = db.get(ServiceRequest, request_id)

    if service_request is None:
        raise HTTPException(
            status_code=404,
            detail="Service request not found.",
        )

    validate_transition(
        service_request.state,
        "VALIDATING",
    )

    service_request.state = "VALIDATING"
    db.flush()

    result = validate_service_request(
        db=db,
        request=service_request,
    )

    if result.valid:
        validate_transition(
            service_request.state,
            "VALIDATED",
        )
        service_request.state = "VALIDATED"
    else:
        validate_transition(
            service_request.state,
            "NEEDS_REVIEW",
        )
        service_request.state = "NEEDS_REVIEW"

    db.commit()
    db.refresh(service_request)

    return {
        "request": service_request,
        "valid": result.valid,
        "issues": result.issues,
    }

@router.post("/{request_id}/classify")
def classify_service_request(
    request_id: int,
    db: Session = Depends(get_db),
):
    request = (
        db.query(ServiceRequest)
        .filter(ServiceRequest.id == request_id)
        .first()
    )

    if request is None:
        raise HTTPException(
            status_code=404,
            detail="Service request not found.",
        )

    result = classify_request(
        title=request.title,
        description=request.description,
        maintenance_mode=request.maintenance_mode,
    )
    existing_analysis = (
        db.query(RequestAIAnalysis)
        .filter(RequestAIAnalysis.request_id == request.id)
        .order_by(RequestAIAnalysis.id.desc())
        .first()
    )
    if existing_analysis:
        analysis = existing_analysis
        analysis.issue_type = result["issue_type"]
        analysis.failure_mode = result["failure_mode"]
        analysis.severity = result["severity"]
        analysis.required_skills = result["required_skills"]
        analysis.required_tools = result["required_tools"]
        analysis.required_parts = result["required_parts"]
        analysis.similar_failures = result["similar_failures"]
        analysis.confidence = result["confidence"]
        analysis.model_name = result["model_name"]
        analysis.analysis_result = result["analysis_result"]
    else:
        analysis = RequestAIAnalysis(
            request_id=request.id,
            issue_type=result["issue_type"],
            failure_mode=result["failure_mode"],
            severity=result["severity"],
            required_skills=result["required_skills"],
            required_tools=result["required_tools"],
            required_parts=result["required_parts"],
            similar_failures=result["similar_failures"],
            confidence=result["confidence"],
            model_name=result["model_name"],
            analysis_result=result["analysis_result"],
        )
        db.add(analysis)
    db.commit()
    db.refresh(analysis)

    return {
        "request_id": request.id,
        "request_code": request.request_code,
        "analysis_id": analysis.id,
        "issue_type": analysis.issue_type,
        "failure_mode": analysis.failure_mode,
        "severity": analysis.severity,
        "required_skills": analysis.required_skills,
        "required_tools": analysis.required_tools,
        "required_parts": analysis.required_parts,
        "confidence": analysis.confidence,
        "model_name": analysis.model_name,
    }

@router.post("/{request_id}/sla")
def calculate_request_sla(
    request_id: int,
    db: Session = Depends(get_db),
):
    service_request = db.get(ServiceRequest, request_id)

    if service_request is None:
        raise HTTPException(
            status_code=404,
            detail="Service request not found.",
        )

    result = calculate_sla(
        priority=service_request.priority,
        travel_minutes=30,
        job_duration_minutes=120,
        resource_wait_minutes=0,
    )

    return {
        "request_id": service_request.id,
        "request_code": service_request.request_code,
        "priority": service_request.priority,
        "deadline": result.deadline,
        "estimated_finish": result.estimated_finish,
        "status": result.status,
        "remaining_minutes": result.remaining_minutes,
    }

@router.post("/{request_id}/plan")
def plan_service_request(
    request_id: int,
    db: Session = Depends(get_db),
):
    service_request = db.get(ServiceRequest, request_id)

    if service_request is None:
        raise HTTPException(
            status_code=404,
            detail="Service request not found.",
        )

    validate_transition(
        service_request.state,
        "PLANNING",
    )

    technicians = (
        db.query(Technician)
        .filter(Technician.is_active == True)
        .all()
    )

    if not technicians:
        raise HTTPException(
            status_code=409,
            detail="No active technicians available.",
        )

    candidates = []

    for technician in technicians:
        if technician.employee_code == "TECH-001":
            factors = MatchingFactors(
                skill_match=100,
                availability=100,
                sla_feasibility=100,
                distance=95,
                familiarity=90,
                workload=90,
                performance=technician.performance_score,
            )
        else:
            factors = MatchingFactors(
                skill_match=75,
                availability=100,
                sla_feasibility=100,
                distance=75,
                familiarity=60,
                workload=50,
                performance=technician.performance_score,
            )

        candidates.append((technician, factors))

    ranked = rank_technicians(db, candidates)

    service_request.state = "PLANNING"
    db.commit()
    db.refresh(service_request)

    return {
        "request_id": service_request.id,
        "request_code": service_request.request_code,
        "state": service_request.state,
        "recommended_technician": {
            "id": ranked[0][0].id,
            "employee_code": ranked[0][0].employee_code,
            "match_score": ranked[0][1],
        },
        "candidates": [
            {
                "technician_id": technician.id,
                "employee_code": technician.employee_code,
                "match_score": score,
            }
            for technician, score in ranked
        ],
    }

@router.post("/{request_id}/resource-check")
def resource_check_service_request(
    request_id: int,
    db: Session = Depends(get_db),
):
    request = (
        db.query(ServiceRequest)
        .filter(ServiceRequest.id == request_id)
        .first()
    )

    if request is None:
        raise HTTPException(
            status_code=404,
            detail="Service request not found.",
        )

    if request.state != ServiceRequestState.PLANNING.value:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Resource check requires PLANNING state. "
                f"Current state: {request.state}"
            ),
        )

    technician = (
        db.query(Technician)
        .filter(
            Technician.is_active.is_(True),
            Technician.employee_code == "TECH-001",
        )
        .first()
    )

    if technician is None:
        raise HTTPException(
            status_code=404,
            detail="Recommended technician not found.",
        )

    result = check_resource_readiness(
        db,
        technician.id,
        [
            {
                "part_id": 1,
                "quantity": 1,
                "warehouse_id": 1,
            },
            {
                "part_id": 2,
                "quantity": 1,
                "warehouse_id": 1,
            },
        ],
    )

    if result["ready"]:
        request.state = ServiceRequestState.RESOURCES_READY.value
    else:
        request.state = ServiceRequestState.BLOCKED_BY_RESOURCE.value

    db.commit()
    db.refresh(request)

    return {
        "request_id": request.id,
        "request_code": request.request_code,
        "state": request.state,
        "technician_id": technician.id,
        "technician_code": technician.employee_code,
        "resource_check": result,
    }

@router.post("/{request_id}/reserve")
def reserve_service_request_resources(
    request_id: int,
    db: Session = Depends(get_db),
):
    request = (
        db.query(ServiceRequest)
        .filter(ServiceRequest.id == request_id)
        .first()
    )

    if request is None:
        raise HTTPException(
            status_code=404,
            detail="Service request not found.",
        )

    if request.state != ServiceRequestState.RESOURCES_READY.value:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Reservation requires RESOURCES_READY state. "
                f"Current state: {request.state}"
            ),
        )

    technician = (
        db.query(Technician)
        .filter(
            Technician.is_active.is_(True),
            Technician.employee_code == "TECH-001",
        )
        .first()
    )

    if technician is None:
        raise HTTPException(
            status_code=404,
            detail="Recommended technician not found.",
        )

    technician_start = (
        request.requested_start_at
        or datetime.now(timezone.utc)
    )

    technician_end = (
        request.requested_end_at
        or technician_start + timedelta(hours=2)
    )

    try:
        result = plan_resources(
            db=db,
            service_request_id=request.id,
            technician_id=technician.id,
            match_score=96.25,
            technician_start_at=technician_start,
            technician_end_at=technician_end,
            parts=[
                {
                    "part_id": 1,
                    "warehouse_id": 1,
                    "quantity": 1,
                },
                {
                    "part_id": 2,
                    "warehouse_id": 2,
                    "quantity": 1,
                },
            ],
        )

        request.state = ServiceRequestState.PENDING_APPROVAL.value

        db.commit()

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=400,
            detail=f"Resource reservation failed: {str(exc)}",
        )

    return {
        "request_id": request.id,
        "request_code": request.request_code,
        "state": request.state,
        "assignment_id": result["assignment"].id,
        "technician_reservation_id": (
            result["technician_reservation"].id
        ),
        "part_reservation_ids": [
            reservation.id
            for reservation in result["part_reservations"]
        ],
    }

@router.post("/{request_id}/approve")
def approve_service_request(
    request_id: int,
    db: Session = Depends(get_db),
):
    request = (
        db.query(ServiceRequest)
        .filter(ServiceRequest.id == request_id)
        .first()
    )

    if request is None:
        raise HTTPException(
            status_code=404,
            detail="Service request not found.",
        )

    if request.state != ServiceRequestState.PENDING_APPROVAL.value:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Approval requires PENDING_APPROVAL state. "
                f"Current state: {request.state}"
            ),
        )

    approval = Approval(
        service_request_id=request.id,
        approved_by=1,
        status="APPROVED",
        comments="Approved by operations manager.",
    )

    db.add(approval)

    request.state = ServiceRequestState.APPROVED.value

    db.commit()
    db.refresh(approval)
    db.refresh(request)

    return {
        "request_id": request.id,
        "request_code": request.request_code,
        "state": request.state,
        "approval_id": approval.id,
        "approved_by": approval.approved_by,
        "status": approval.status,
    }

@router.post("/{request_id}/dispatch")
def dispatch_service_request(
    request_id: int,
    db: Session = Depends(get_db),
):
    request = (
        db.query(ServiceRequest)
        .filter(ServiceRequest.id == request_id)
        .first()
    )

    if request is None:
        raise HTTPException(
            status_code=404,
            detail="Service request not found.",
        )

    if request.state != ServiceRequestState.APPROVED.value:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Dispatch requires APPROVED state. "
                f"Current state: {request.state}"
            ),
        )

    assignment = (
        db.query(Assignment)
        .filter(
            Assignment.service_request_id == request.id,
            Assignment.status == "PROPOSED",
        )
        .order_by(Assignment.id.desc())
        .first()
    )

    if assignment is None:
        raise HTTPException(
            status_code=404,
            detail="No proposed assignment found.",
        )

    assignment.status = "ASSIGNED"
    assignment.assigned_at = datetime.now(timezone.utc)

    request.state = ServiceRequestState.DISPATCHED.value

    db.commit()
    db.refresh(assignment)
    db.refresh(request)

    return {
        "request_id": request.id,
        "request_code": request.request_code,
        "state": request.state,
        "assignment_id": assignment.id,
        "technician_id": assignment.technician_id,
        "assignment_status": assignment.status,
        "assigned_at": assignment.assigned_at,
    }

@router.post("/{request_id}/approve-reassignment")
def approve_reassignment(
    request_id: int,
    db: Session = Depends(get_db),
):
    request = (
        db.query(ServiceRequest)
        .filter(ServiceRequest.id == request_id)
        .first()
    )

    if request is None:
        raise HTTPException(
            status_code=404,
            detail="Service request not found.",
        )

    assignment = (
        db.query(Assignment)
        .filter(
            Assignment.service_request_id == request.id,
            Assignment.status == "PROPOSED",
        )
        .order_by(Assignment.id.desc())
        .first()
    )

    if assignment is None:
        raise HTTPException(
            status_code=404,
            detail="No proposed reassignment found.",
        )

    assignment.status = "ASSIGNED"
    assignment.assigned_at = datetime.now(timezone.utc)

    approval = Approval(
        service_request_id=request.id,
        approved_by=1,
        status="APPROVED",
        comments="Dynamic reassignment approved.",
    )

    db.add(approval)

    db.commit()
    db.refresh(assignment)
    db.refresh(approval)

    return {
        "request_id": request.id,
        "request_code": request.request_code,
        "assignment_id": assignment.id,
        "technician_id": assignment.technician_id,
        "assignment_status": assignment.status,
        "assigned_at": assignment.assigned_at,
        "approval_id": approval.id,
        "approval_status": approval.status,
        "message": "Reassignment approved successfully.",
    }

@router.post("/{request_id}/accept")
def accept_service_request(
    request_id: int,
    db: Session = Depends(get_db),
):
    request = (
        db.query(ServiceRequest)
        .filter(ServiceRequest.id == request_id)
        .first()
    )

    if request is None:
        raise HTTPException(
            status_code=404,
            detail="Service request not found.",
        )

    if request.state != ServiceRequestState.DISPATCHED.value:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Acceptance requires DISPATCHED state. "
                f"Current state: {request.state}"
            ),
        )

    assignment = (
        db.query(Assignment)
        .filter(
            Assignment.service_request_id == request.id,
            Assignment.status == "ASSIGNED",
        )
        .order_by(Assignment.id.desc())
        .first()
    )

    if assignment is None:
        raise HTTPException(
            status_code=404,
            detail="No assigned technician found.",
        )

    now = datetime.now(timezone.utc)

    assignment.status = "ACCEPTED"
    assignment.accepted_at = now

    request.state = ServiceRequestState.ACCEPTED_BY_TECH.value

    db.commit()
    db.refresh(assignment)
    db.refresh(request)

    return {
        "request_id": request.id,
        "request_code": request.request_code,
        "state": request.state,
        "assignment_id": assignment.id,
        "technician_id": assignment.technician_id,
        "assignment_status": assignment.status,
        "accepted_at": assignment.accepted_at,
    }

@router.post("/{request_id}/check-in")
def technician_check_in(
    request_id: int,
    db: Session = Depends(get_db),
):
    request = (
        db.query(ServiceRequest)
        .filter(ServiceRequest.id == request_id)
        .first()
    )

    if request is None:
        raise HTTPException(
            status_code=404,
            detail="Service request not found.",
        )

    if request.state != ServiceRequestState.ACCEPTED_BY_TECH.value:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Check-in requires ACCEPTED_BY_TECH state. "
                f"Current state: {request.state}"
            ),
        )

    assignment = (
        db.query(Assignment)
        .filter(
            Assignment.service_request_id == request.id,
            Assignment.status == "ACCEPTED",
        )
        .order_by(Assignment.id.desc())
        .first()
    )

    if assignment is None:
        raise HTTPException(
            status_code=404,
            detail="No accepted technician assignment found.",
        )

    work_log = WorkLog(
        service_request_id=request.id,
        technician_id=assignment.technician_id,
        log_type="CHECK_IN",
        description="Technician checked in at the service site.",
    )

    db.add(work_log)
    db.commit()
    db.refresh(work_log)

    return {
        "request_id": request.id,
        "request_code": request.request_code,
        "state": request.state,
        "assignment_id": assignment.id,
        "technician_id": assignment.technician_id,
        "work_log_id": work_log.id,
        "log_type": work_log.log_type,
        "message": "Technician check-in recorded.",
    }

@router.post("/{request_id}/start-work")
def start_service_request_work(
    request_id: int,
    db: Session = Depends(get_db),
):
    request = (
        db.query(ServiceRequest)
        .filter(ServiceRequest.id == request_id)
        .first()
    )

    if request is None:
        raise HTTPException(
            status_code=404,
            detail="Service request not found.",
        )

    if request.state != ServiceRequestState.ACCEPTED_BY_TECH.value:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Start work requires ACCEPTED_BY_TECH state. "
                f"Current state: {request.state}"
            ),
        )

    assignment = (
        db.query(Assignment)
        .filter(
            Assignment.service_request_id == request.id,
            Assignment.status == "ACCEPTED",
        )
        .order_by(Assignment.id.desc())
        .first()
    )

    if assignment is None:
        raise HTTPException(
            status_code=404,
            detail="No accepted technician assignment found.",
        )

    machine = (
        db.query(Machine)
        .filter(Machine.id == request.machine_id)
        .first()
    )

    if machine is None:
        raise HTTPException(
            status_code=404,
            detail="Machine not found.",
        )

    work_log = WorkLog(
        service_request_id=request.id,
        technician_id=assignment.technician_id,
        log_type="START_WORK",
        description="Technician started maintenance work.",
    )

    db.add(work_log)

    checklist = create_work_checklist(
        db=db,
        service_request_id=request.id,
        maintenance_mode=request.maintenance_mode,
        machine_type="DM-X100",
    )

    request.state = ServiceRequestState.IN_PROGRESS.value

    db.commit()

    db.refresh(work_log)
    db.refresh(request)

    return {
        "request_id": request.id,
        "request_code": request.request_code,
        "state": request.state,
        "assignment_id": assignment.id,
        "technician_id": assignment.technician_id,
        "work_log_id": work_log.id,
        "log_type": work_log.log_type,
        "checklist_count": len(checklist),
        "message": "Maintenance work started.",
    }

@router.post("/{request_id}/work-log")
def create_work_log(
    request_id: int,
    payload: WorkLogCreate,
    db: Session = Depends(get_db),
):
    request = (
        db.query(ServiceRequest)
        .filter(ServiceRequest.id == request_id)
        .first()
    )

    if request is None:
        raise HTTPException(
            status_code=404,
            detail="Service request not found.",
        )

    if request.state != ServiceRequestState.IN_PROGRESS.value:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Work logs require IN_PROGRESS state. "
                f"Current state: {request.state}"
            ),
        )

    assignment = (
        db.query(Assignment)
        .filter(
            Assignment.service_request_id == request.id,
            Assignment.status == "ACCEPTED",
        )
        .order_by(Assignment.id.desc())
        .first()
    )

    if assignment is None:
        raise HTTPException(
            status_code=404,
            detail="No accepted technician assignment found.",
        )

    work_log = WorkLog(
        service_request_id=request.id,
        technician_id=assignment.technician_id,
        log_type=payload.log_type,
        description=payload.description,
    )

    db.add(work_log)
    db.commit()
    db.refresh(work_log)

    return {
        "request_id": request.id,
        "request_code": request.request_code,
        "state": request.state,
        "work_log_id": work_log.id,
        "technician_id": assignment.technician_id,
        "log_type": work_log.log_type,
        "description": work_log.description,
        "created_at": work_log.created_at,
    }

@router.post("/{request_id}/part-usage")
def record_part_usage(
    request_id: int,
    payload: PartUsageCreate,
    db: Session = Depends(get_db),
):
    request = (
        db.query(ServiceRequest)
        .filter(ServiceRequest.id == request_id)
        .first()
    )

    if request is None:
        raise HTTPException(
            status_code=404,
            detail="Service request not found.",
        )

    if request.state != ServiceRequestState.IN_PROGRESS.value:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Part usage requires IN_PROGRESS state. "
                f"Current state: {request.state}"
            ),
        )

    assignment = (
        db.query(Assignment)
        .filter(
            Assignment.service_request_id == request.id,
            Assignment.status == "ACCEPTED",
        )
        .order_by(Assignment.id.desc())
        .first()
    )

    if assignment is None:
        raise HTTPException(
            status_code=404,
            detail="No accepted technician assignment found.",
        )

    try:
        usage = consume_reserved_part(
            db=db,
            service_request_id=request.id,
            assignment_id=assignment.id,
            part_id=payload.part_id,
            warehouse_id=payload.warehouse_id,
            quantity=payload.quantity,
            recorded_by=1,
        )

        db.commit()
        db.refresh(usage)

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    return {
        "request_id": request.id,
        "request_code": request.request_code,
        "assignment_id": assignment.id,
        "part_usage_id": usage.id,
        "part_id": usage.part_id,
        "warehouse_id": usage.warehouse_id,
        "quantity": usage.quantity,
        "usage_type": usage.usage_type,
        "recorded_by": usage.recorded_by,
        "created_at": usage.created_at,
        "message": "Part consumption recorded successfully.",
    }

@router.get("/{request_id}/checklist")
def get_service_request_checklist(
    request_id: int,
    db: Session = Depends(get_db),
):
    request = (
        db.query(ServiceRequest)
        .filter(ServiceRequest.id == request_id)
        .first()
    )

    if request is None:
        raise HTTPException(
            status_code=404,
            detail="Service request not found.",
        )

    checklist_rows = (
        db.query(WorkChecklist, ChecklistItem)
        .join(
            ChecklistItem,
            WorkChecklist.checklist_item_id == ChecklistItem.id,
        )
        .filter(
            WorkChecklist.service_request_id == request_id
        )
        .order_by(ChecklistItem.sequence)
        .all()
    )

    return {
        "request_id": request.id,
        "request_code": request.request_code,
        "state": request.state,
        "total_items": len(checklist_rows),
        "completed_items": sum(
            1 for work_item, _ in checklist_rows
            if work_item.completed
        ),
        "items": [
            {
                "id": work_item.id,
                "checklist_item_id": item.id,
                "sequence": item.sequence,
                "item_text": item.item_text,
                "is_mandatory": item.is_mandatory,
                "completed": work_item.completed,
                "completed_by": work_item.completed_by,
                "completed_at": work_item.completed_at,
                "notes": work_item.notes,
            }
            for work_item, item in checklist_rows
        ],
    }

@router.post("/{request_id}/checklist/{checklist_id}/complete")
def complete_checklist_item(
    request_id: int,
    checklist_id: int,
    payload: ChecklistComplete,
    db: Session = Depends(get_db),
):
    request = (
        db.query(ServiceRequest)
        .filter(ServiceRequest.id == request_id)
        .first()
    )

    if request is None:
        raise HTTPException(
            status_code=404,
            detail="Service request not found.",
        )

    if request.state != ServiceRequestState.IN_PROGRESS.value:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Checklist completion requires IN_PROGRESS state. "
                f"Current state: {request.state}"
            ),
        )

    work_item = (
        db.query(WorkChecklist)
        .filter(
            WorkChecklist.id == checklist_id,
            WorkChecklist.service_request_id == request_id,
        )
        .first()
    )

    if work_item is None:
        raise HTTPException(
            status_code=404,
            detail="Checklist item not found.",
        )

    if work_item.completed:
        raise HTTPException(
            status_code=400,
            detail="Checklist item is already completed.",
        )

    assignment = (
        db.query(Assignment)
        .filter(
            Assignment.service_request_id == request_id,
            Assignment.status == "ACCEPTED",
        )
        .order_by(Assignment.id.desc())
        .first()
    )

    if assignment is None:
        raise HTTPException(
            status_code=404,
            detail="No accepted technician assignment found.",
        )

    work_item.completed = True
    work_item.completed_by = (
        db.query(Technician)
        .filter(Technician.id == assignment.technician_id)
        .first()
        .user_id
    )
    work_item.completed_at = datetime.now(timezone.utc)
    work_item.notes = payload.notes
    db.commit()
    db.refresh(work_item)

    return {
        "request_id": request.id,
        "request_code": request.request_code,
        "state": request.state,
        "checklist_id": work_item.id,
        "completed": work_item.completed,
        "completed_by": work_item.completed_by,
        "completed_at": work_item.completed_at,
        "notes": work_item.notes,
        "message": "Checklist item completed.",
    }

@router.post("/{request_id}/complete")
def complete_service_request(
    request_id: int,
    db: Session = Depends(get_db),
):
    request = (
        db.query(ServiceRequest)
        .filter(ServiceRequest.id == request_id)
        .first()
    )

    if request is None:
        raise HTTPException(
            status_code=404,
            detail="Service request not found.",
        )

    if request.state != ServiceRequestState.IN_PROGRESS.value:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Completion requires IN_PROGRESS state. "
                f"Current state: {request.state}"
            ),
        )

    checklist_rows = (
        db.query(WorkChecklist, ChecklistItem)
        .join(
            ChecklistItem,
            WorkChecklist.checklist_item_id == ChecklistItem.id,
        )
        .filter(
            WorkChecklist.service_request_id == request_id
        )
        .all()
    )

    mandatory_items = [
        work_item
        for work_item, checklist_item in checklist_rows
        if checklist_item.is_mandatory
    ]

    incomplete_items = [
        work_item.id
        for work_item in mandatory_items
        if not work_item.completed
    ]

    if incomplete_items:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Mandatory checklist items are incomplete.",
                "incomplete_checklist_ids": incomplete_items,
            },
        )

    request.state = (
        ServiceRequestState.COMPLETED_PENDING_VERIFICATION.value
    )

    db.commit()
    db.refresh(request)

    return {
        "request_id": request.id,
        "request_code": request.request_code,
        "state": request.state,
        "checklist_total": len(checklist_rows),
        "mandatory_items": len(mandatory_items),
        "message": "Maintenance work completed and pending verification.",
    }

@router.post("/{request_id}/verify")
def verify_service_request(
    request_id: int,
    db: Session = Depends(get_db),
):
    request = (
        db.query(ServiceRequest)
        .filter(ServiceRequest.id == request_id)
        .first()
    )

    if request is None:
        raise HTTPException(
            status_code=404,
            detail="Service request not found.",
        )

    if request.state != ServiceRequestState.COMPLETED_PENDING_VERIFICATION.value:
        raise HTTPException(
            status_code=400,
            detail=(
                "Verification requires COMPLETED_PENDING_VERIFICATION state. "
                f"Current state: {request.state}"
            ),
        )

    checklist_rows = (
        db.query(WorkChecklist, ChecklistItem)
        .join(
            ChecklistItem,
            WorkChecklist.checklist_item_id == ChecklistItem.id,
        )
        .filter(
            WorkChecklist.service_request_id == request_id
        )
        .all()
    )

    mandatory_items = [
        work_item
        for work_item, checklist_item in checklist_rows
        if checklist_item.is_mandatory
    ]

    incomplete_items = [
        work_item.id
        for work_item in mandatory_items
        if not work_item.completed
    ]

    if incomplete_items:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Verification failed because mandatory checklist items are incomplete.",
                "incomplete_checklist_ids": incomplete_items,
            },
        )

    evidence_count = (
        db.query(Attachment)
        .filter(
            Attachment.service_request_id == request.id,
            Attachment.attachment_type == "EVIDENCE",
        )
        .count()
    )

    if evidence_count == 0:
        raise HTTPException(
            status_code=400,
            detail="Completion verification requires at least one evidence attachment.",
        )

    assignment = (
        db.query(Assignment)
        .filter(
            Assignment.service_request_id == request_id,
            Assignment.status == "ACCEPTED",
        )
        .order_by(Assignment.id.desc())
        .first()
    )

    if assignment is None:
        raise HTTPException(
            status_code=404,
            detail="Accepted technician assignment not found.",
        )

    request.state = ServiceRequestState.VERIFICATION.value
    db.commit()

    request.state = ServiceRequestState.PASSED.value
    db.commit()

    db.refresh(request)

    return {
        "request_id": request.id,
        "request_code": request.request_code,
        "state": request.state,
        "assignment_id": assignment.id,
        "technician_id": assignment.technician_id,
        "checklist_total": len(checklist_rows),
        "mandatory_items": len(mandatory_items),
        "evidence_count": evidence_count,
        "message": "Service verification passed.",
    }


@router.post("/{request_id}/customer-approve")
def customer_approve_service_request(
    request_id: int,
    db: Session = Depends(get_db),
):
    request = (
        db.query(ServiceRequest)
        .filter(ServiceRequest.id == request_id)
        .first()
    )

    if request is None:
        raise HTTPException(
            status_code=404,
            detail="Service request not found.",
        )

    if request.state != ServiceRequestState.PASSED.value:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Customer approval requires PASSED state. "
                f"Current state: {request.state}"
            ),
        )

    request.state = ServiceRequestState.CUSTOMER_APPROVAL.value

    db.commit()
    db.refresh(request)

    return {
        "request_id": request.id,
        "request_code": request.request_code,
        "state": request.state,
        "message": "Customer approval recorded.",
    }

@router.post("/{request_id}/close")
def close_service_request(
    request_id: int,
    db: Session = Depends(get_db),
):
    request = (
        db.query(ServiceRequest)
        .filter(ServiceRequest.id == request_id)
        .first()
    )

    if request is None:
        raise HTTPException(
            status_code=404,
            detail="Service request not found.",
        )

    if request.state != ServiceRequestState.CUSTOMER_APPROVAL.value:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Closure requires CUSTOMER_APPROVAL state. "
                f"Current state: {request.state}"
            ),
        )

    assignment = (
        db.query(Assignment)
        .filter(
            Assignment.service_request_id == request_id,
            Assignment.status == "ACCEPTED",
        )
        .order_by(Assignment.id.desc())
        .first()
    )

    if assignment is None:
        raise HTTPException(
            status_code=404,
            detail="Accepted technician assignment not found.",
        )

    assignment.status = "COMPLETED"
    assignment.completed_at = datetime.now(timezone.utc)

    request.state = ServiceRequestState.CLOSED.value
    history = create_service_history(db, request.id)
    db.commit()
    db.refresh(request)
    db.refresh(assignment)

    return {
        "request_id": request.id,
        "request_code": request.request_code,
        "state": request.state,
        "assignment_id": assignment.id,
        "technician_id": assignment.technician_id,
        "assignment_status": assignment.status,
        "completed_at": assignment.completed_at,
        "message": "Service request closed successfully.",
    }

@router.post("/{request_id}/simulate-technician-dropout")
def simulate_technician_dropout(
    request_id: int,
    db: Session = Depends(get_db),
):
    request = (
        db.query(ServiceRequest)
        .filter(ServiceRequest.id == request_id)
        .first()
    )

    if not request:
        raise HTTPException(
            status_code=404,
            detail="Service request not found",
        )

    assignment = (
        db.query(Assignment)
        .filter(
            Assignment.service_request_id == request_id,
            Assignment.status.in_(["ASSIGNED", "ACCEPTED"]),
        )
        .order_by(Assignment.id.desc())
        .first()
    )

    if not assignment:
        raise HTTPException(
            status_code=400,
            detail="No active assignment found for this request",
        )

    technician = (
        db.query(Technician)
        .filter(Technician.id == assignment.technician_id)
        .first()
    )

    if not technician:
        raise HTTPException(
            status_code=404,
            detail="Assigned technician not found",
        )

    technician_availability = (
        db.query(TechnicianAvailability)
        .filter(
            TechnicianAvailability.technician_id == technician.id
        )
        .order_by(TechnicianAvailability.id.desc())
        .first()
    )

    if technician_availability:
        technician_availability.status = "UNAVAILABLE"

    exception_event = detect_technician_dropout(
        db=db,
        service_request_id=request.id,
        technician_id=technician.id,
    )

    assignment.status = "DROPPED"

    db.commit()
    db.refresh(exception_event)

    return {
        "request_id": request.id,
        "request_code": request.request_code,
        "assignment_id": assignment.id,
        "technician_id": technician.id,
        "technician_code": technician.technician_code,
        "technician_status": "UNAVAILABLE",
        "assignment_status": assignment.status,
        "exception_id": exception_event.id,
        "exception_type": exception_event.exception_type,
        "severity": exception_event.severity,
        "exception_status": exception_event.status,
        "message": "Technician dropout detected successfully.",
    }

@router.post("/{request_id}/attachments")
def upload_service_request_attachment(
    request_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    request = (
        db.query(ServiceRequest)
        .filter(ServiceRequest.id == request_id)
        .first()
    )

    if request is None:
        raise HTTPException(
            status_code=404,
            detail="Service request not found.",
        )

    try:
        attachment = save_attachment(
            db=db,
            service_request_id=request.id,
            uploaded_by=1,
            file=file,
        )

        db.commit()
        db.refresh(attachment)

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    return {
        "attachment_id": attachment.id,
        "request_id": attachment.service_request_id,
        "file_name": attachment.file_name,
        "content_type": attachment.content_type,
        "file_size": attachment.file_size,
        "attachment_type": attachment.attachment_type,
        "message": "Attachment uploaded successfully.",
    }

@router.get("/{request_id}/attachments")
def list_service_request_attachments(
    request_id: int,
    db: Session = Depends(get_db),
):
    request = (
        db.query(ServiceRequest)
        .filter(ServiceRequest.id == request_id)
        .first()
    )

    if not request:
        raise HTTPException(status_code=404, detail="Service request not found")

    attachments = (
        db.query(Attachment)
        .filter(Attachment.service_request_id == request.id)
        .order_by(Attachment.created_at.asc())
        .all()
    )

    return [
        {
            "attachment_id": attachment.id,
            "request_id": attachment.service_request_id,
            "file_name": attachment.file_name,
            "content_type": attachment.content_type,
            "file_size": attachment.file_size,
            "attachment_type": attachment.attachment_type,
            "created_at": attachment.created_at,
        }
        for attachment in attachments
    ]

@router.get("/{request_id}/attachments/{attachment_id}")
def download_service_request_attachment(
    request_id: int,
    attachment_id: int,
    db: Session = Depends(get_db),
):
    attachment = (
        db.query(Attachment)
        .filter(
            Attachment.id == attachment_id,
            Attachment.service_request_id == request_id,
        )
        .first()
    )

    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    file_path = Path(attachment.file_path)

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Attachment file not found")

    return FileResponse(
        path=file_path,
        media_type=attachment.content_type,
        filename=attachment.file_name,
    )
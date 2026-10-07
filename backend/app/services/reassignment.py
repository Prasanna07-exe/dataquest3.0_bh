from sqlalchemy.orm import Session

from app.models.service_request import ServiceRequest
from app.models.technician import Technician, TechnicianSkill, TechnicianAvailability
from app.services.matching import MatchingFactors, rank_technicians


def find_replacement_candidates(
    db: Session,
    service_request_id: int,
    excluded_technician_id: int,
):
    request = (
        db.query(ServiceRequest)
        .filter(ServiceRequest.id == service_request_id)
        .first()
    )

    if not request:
        return []

    technicians = (
        db.query(Technician)
        .filter(
            Technician.id != excluded_technician_id,
            Technician.is_active.is_(True),
        )
        .all()
    )

    candidates = []

    for technician in technicians:
        availability = (
            db.query(TechnicianAvailability)
            .filter(
                TechnicianAvailability.technician_id == technician.id,
                TechnicianAvailability.status == "AVAILABLE",
            )
            .order_by(TechnicianAvailability.id.desc())
            .first()
        )

        if not availability:
            continue

        skills = (
            db.query(TechnicianSkill)
            .filter(TechnicianSkill.technician_id == technician.id)
            .all()
        )

        has_mechanical_skill = any(
            skill.skill_id == 2
            for skill in skills
        )

        if not has_mechanical_skill:
            continue

        candidates.append(
            (
                technician,
                MatchingFactors(
                    skill_match=75.0,
                    availability=100.0,
                    sla_feasibility=90.0,
                    distance=85.0,
                    familiarity=70.0,
                    workload=max(
                        0.0,
                        100.0 - float(technician.workload_score or 0),
                    ),
                    performance=float(
                        technician.performance_score or 0
                    ),
                ),
            )
        )

    if not candidates:
        return []

    ranked = rank_technicians(db, candidates)

    return ranked

def create_reassignment(db: Session, service_request_id: int, old_assignment_id: int):
    from app.models.assignment import Assignment
    from app.models.reservation import ResourceReservation
    from datetime import datetime, timezone

    old_assignment = (
        db.query(Assignment)
        .filter(Assignment.id == old_assignment_id)
        .first()
    )

    if not old_assignment:
        return None

    candidates = find_replacement_candidates(
        db,
        service_request_id,
        old_assignment.technician_id,
    )

    if not candidates:
        return None

    replacement_technician, score = candidates[0]
    existing_proposed = (
        db.query(Assignment)
        .filter(
            Assignment.service_request_id == service_request_id,
            Assignment.status == "PROPOSED",
        )
        .all()
    )

    for assignment in existing_proposed:
        assignment.status = "CANCELLED"
    new_assignment = Assignment(
        service_request_id=service_request_id,
        technician_id=replacement_technician.id,
        status="PROPOSED",
        match_score=score,
    )

    db.add(new_assignment)
    db.flush()

    old_reservation = (
        db.query(ResourceReservation)
        .filter(
            ResourceReservation.service_request_id == service_request_id,
            ResourceReservation.assignment_id == old_assignment_id,
            ResourceReservation.resource_type == "TECHNICIAN",
            ResourceReservation.status == "RESERVED",
        )
        .first()
    )

    if old_reservation:
        old_reservation.status = "RELEASED"
        old_reservation.released_at = datetime.now(timezone.utc)

        new_reservation = ResourceReservation(
            service_request_id=service_request_id,
            assignment_id=new_assignment.id,
            resource_type="TECHNICIAN",
            resource_id=replacement_technician.id,
            quantity=1,
            start_at=old_reservation.start_at,
            end_at=old_reservation.end_at,
            status="RESERVED",
            notes="Technician reservation created during dynamic reassignment.",
        )

        db.add(new_reservation)

    return new_assignment
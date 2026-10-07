from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.models.assignment import Assignment
from app.models.reservation import ResourceReservation
from app.services.inventory import reserve_part

def begin_orchestration_transaction(db: Session) -> None:
    if db.in_transaction():
        return

    db.begin()

def create_assignment(
    db: Session,
    service_request_id: int,
    technician_id: int,
    match_score: float,
) -> Assignment:
    if not 0 <= match_score <= 100:
        raise ValueError("Match score must be between 0 and 100.")

    assignment = Assignment(
        service_request_id=service_request_id,
        technician_id=technician_id,
        status="PROPOSED",
        match_score=match_score,
        created_at=datetime.now(timezone.utc),
    )

    db.add(assignment)
    db.flush()

    return assignment

def reserve_technician(
    db: Session,
    service_request_id: int,
    assignment_id: int,
    technician_id: int,
    start_at: datetime,
    end_at: datetime,
) -> ResourceReservation:
    if end_at <= start_at:
        raise ValueError("Reservation end time must be after start time.")

    reservation = ResourceReservation(
        service_request_id=service_request_id,
        assignment_id=assignment_id,
        resource_type="TECHNICIAN",
        resource_id=technician_id,
        quantity=1,
        start_at=start_at,
        end_at=end_at,
        status="RESERVED",
        created_at=datetime.now(timezone.utc),
    )

    db.add(reservation)
    db.flush()

    return reservation

def reserve_part_resource(
    db: Session,
    service_request_id: int,
    part_id: int,
    warehouse_id: int,
    quantity: int,
) -> ResourceReservation:
    if quantity <= 0:
        raise ValueError("Part quantity must be greater than zero.")

    reserve_part(
        db=db,
        warehouse_id=warehouse_id,
        part_id=part_id,
        quantity=quantity,
    )

    reservation = ResourceReservation(
        service_request_id=service_request_id,
        assignment_id=None,
        resource_type="PART",
        resource_id=part_id,
        quantity=quantity,
        status="RESERVED",
        created_at=datetime.now(timezone.utc),
    )

    db.add(reservation)
    db.flush()

    return reservation

def plan_resources(
    db: Session,
    service_request_id: int,
    technician_id: int,
    match_score: float,
    technician_start_at: datetime,
    technician_end_at: datetime,
    parts: list[dict],
):
    begin_orchestration_transaction(db)

    assignment = create_assignment(
        db=db,
        service_request_id=service_request_id,
        technician_id=technician_id,
        match_score=match_score,
    )

    technician_reservation = reserve_technician(
        db=db,
        service_request_id=service_request_id,
        assignment_id=assignment.id,
        technician_id=technician_id,
        start_at=technician_start_at,
        end_at=technician_end_at,
    )

    part_reservations = []

    for part in parts:
        reservation = reserve_part_resource(
            db=db,
            service_request_id=service_request_id,
            part_id=part["part_id"],
            warehouse_id=part["warehouse_id"],
            quantity=part["quantity"],
        )
        part_reservations.append(reservation)

    return {
        "assignment": assignment,
        "technician_reservation": technician_reservation,
        "part_reservations": part_reservations,
    }
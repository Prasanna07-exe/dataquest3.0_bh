from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.inventory import InventoryBalance
from datetime import datetime

from app.models.part_usage import PartUsage
from app.models.reservation import ResourceReservation

@dataclass
class InventoryAvailability:
    warehouse_id: int
    part_id: int
    quantity_on_hand: int
    quantity_reserved: int
    quantity_available: int
    sufficient: bool


def check_part_availability(
    db: Session,
    warehouse_id: int,
    part_id: int,
    required_quantity: int,
) -> InventoryAvailability:
    balance = db.scalar(
        select(InventoryBalance).where(
            InventoryBalance.warehouse_id == warehouse_id,
            InventoryBalance.part_id == part_id,
        )
    )

    if balance is None:
        return InventoryAvailability(
            warehouse_id=warehouse_id,
            part_id=part_id,
            quantity_on_hand=0,
            quantity_reserved=0,
            quantity_available=0,
            sufficient=False,
        )

    quantity_available = max(
        0,
        balance.quantity_on_hand - balance.quantity_reserved,
    )

    return InventoryAvailability(
        warehouse_id=warehouse_id,
        part_id=part_id,
        quantity_on_hand=balance.quantity_on_hand,
        quantity_reserved=balance.quantity_reserved,
        quantity_available=quantity_available,
        sufficient=quantity_available >= required_quantity,
    )

def reserve_part(
    db: Session,
    warehouse_id: int,
    part_id: int,
    quantity: int,
) -> InventoryBalance:
    if quantity <= 0:
        raise ValueError("Reservation quantity must be greater than zero.")

    balance = db.scalar(
        select(InventoryBalance)
        .where(
            InventoryBalance.warehouse_id == warehouse_id,
            InventoryBalance.part_id == part_id,
        )
        .with_for_update()
    )

    if balance is None:
        raise ValueError("Inventory balance does not exist.")

    quantity_available = (
        balance.quantity_on_hand - balance.quantity_reserved
    )

    if quantity_available < quantity:
        raise ValueError(
            f"Insufficient inventory. "
            f"Available: {quantity_available}, requested: {quantity}."
        )

    balance.quantity_reserved += quantity

    return balance

def consume_reserved_part(
    db: Session,
    service_request_id: int,
    assignment_id: int | None,
    part_id: int,
    warehouse_id: int,
    quantity: int,
    recorded_by: int,
) -> PartUsage:
    if quantity <= 0:
        raise ValueError("Consumption quantity must be greater than zero.")

    balance = db.scalar(
        select(InventoryBalance)
        .where(
            InventoryBalance.warehouse_id == warehouse_id,
            InventoryBalance.part_id == part_id,
        )
        .with_for_update()
    )

    if balance is None:
        raise ValueError("Inventory balance does not exist.")

    if balance.quantity_on_hand < quantity:
        raise ValueError(
            f"Insufficient stock. "
            f"On hand: {balance.quantity_on_hand}, requested: {quantity}."
        )

    reservation_query = (
        select(ResourceReservation)
        .where(
            ResourceReservation.service_request_id == service_request_id,
            ResourceReservation.resource_type == "PART",
            ResourceReservation.resource_id == part_id,
            ResourceReservation.status == "RESERVED",
        )
        .with_for_update()
    )

    reservation = db.scalar(reservation_query)

    if reservation is None:
        raise ValueError(
            "No active part reservation found for this service request."
        )

    if reservation.quantity < quantity:
        raise ValueError(
            f"Reserved quantity is insufficient. "
            f"Reserved: {reservation.quantity}, requested: {quantity}."
        )

    balance.quantity_on_hand -= quantity
    balance.quantity_reserved -= quantity

    reservation.quantity -= quantity

    if reservation.quantity == 0:
        reservation.status = "CONSUMED"
        reservation.released_at = datetime.utcnow()

    usage = PartUsage(
        service_request_id=service_request_id,
        assignment_id=assignment_id,
        part_id=part_id,
        warehouse_id=warehouse_id,
        quantity=quantity,
        usage_type="CONSUMED",
        recorded_by=recorded_by,
    )

    db.add(usage)
    db.flush()

    return usage

def find_alternate_warehouses(
    db: Session,
    part_id: int,
    required_quantity: int,
    exclude_warehouse_id: int | None = None,
) -> list[InventoryAvailability]:
    query = (
        select(InventoryBalance)
        .where(
            InventoryBalance.part_id == part_id,
        )
        .order_by(InventoryBalance.quantity_on_hand)
    )

    balances = db.scalars(query).all()

    alternatives: list[InventoryAvailability] = []

    for balance in balances:
        if (
            exclude_warehouse_id is not None
            and balance.warehouse_id == exclude_warehouse_id
        ):
            continue

        quantity_available = max(
            0,
            balance.quantity_on_hand - balance.quantity_reserved,
        )

        alternatives.append(
            InventoryAvailability(
                warehouse_id=balance.warehouse_id,
                part_id=balance.part_id,
                quantity_on_hand=balance.quantity_on_hand,
                quantity_reserved=balance.quantity_reserved,
                quantity_available=quantity_available,
                sufficient=quantity_available >= required_quantity,
            )
        )

    alternatives.sort(
        key=lambda item: item.quantity_available,
        reverse=True,
    )

    return alternatives


from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.inventory import InventoryBalance


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


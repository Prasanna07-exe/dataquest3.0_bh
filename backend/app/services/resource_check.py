from sqlalchemy.orm import Session

from app.models.technician import Technician, TechnicianAvailability
from app.models.inventory import InventoryBalance
from app.services.inventory import find_alternate_warehouses


def check_resource_readiness(
    db: Session,
    technician_id: int,
    required_parts: list[dict],
) -> dict:
    technician = (
        db.query(Technician)
        .filter(
            Technician.id == technician_id,
            Technician.is_active.is_(True),
        )
        .first()
    )

    if not technician:
        return {
            "ready": False,
            "technician_ready": False,
            "issues": ["Technician not found or inactive."],
            "parts": [],
        }

    availability = (
        db.query(TechnicianAvailability)
        .filter(
            TechnicianAvailability.technician_id == technician_id,
            TechnicianAvailability.status == "AVAILABLE",
        )
        .first()
    )

    technician_ready = availability is not None
    issues = []

    if not technician_ready:
        issues.append("Technician is not currently available.")

    part_results = []

    for required in required_parts:
        part_id = required["part_id"]
        quantity = required["quantity"]
        warehouse_id = required.get("warehouse_id")

        query = db.query(InventoryBalance).filter(
            InventoryBalance.part_id == part_id
        )

        if warehouse_id is not None:
            query = query.filter(
                InventoryBalance.warehouse_id == warehouse_id
            )

        inventory = query.first()

        available_quantity = 0

        if inventory:
            available_quantity = max(
                0,
                inventory.quantity_on_hand
                - inventory.quantity_reserved,
            )

        if available_quantity >= quantity:
            part_results.append(
                {
                    "part_id": part_id,
                    "required_quantity": quantity,
                    "available_quantity": available_quantity,
                    "status": "AVAILABLE",
                    "alternate_warehouse_id": None,
                }
            )
            continue

        alternatives = find_alternate_warehouses(
            db,
            part_id,
            quantity,
            exclude_warehouse_id=warehouse_id,
        )

        alternate = next(
            (
                item
                for item in alternatives
                if item.sufficient
            ),
            None,
        )

        if alternate:
            status = "ALTERNATE_WAREHOUSE"
            alternate_warehouse_id = alternate.warehouse_id
        else:
            status = "SHORTAGE"
            alternate_warehouse_id = None

        part_results.append(
            {
                "part_id": part_id,
                "required_quantity": quantity,
                "available_quantity": available_quantity,
                "status": status,
                "alternate_warehouse_id": alternate_warehouse_id,
            }
        )

        if status == "SHORTAGE":
            issues.append(
                f"Part {part_id} has insufficient inventory."
            )

    ready = technician_ready and all(
        item["status"] != "SHORTAGE"
        for item in part_results
    )

    return {
        "ready": ready,
        "technician_ready": technician_ready,
        "issues": issues,
        "parts": part_results,
    }
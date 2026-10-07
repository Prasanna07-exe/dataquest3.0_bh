from sqlalchemy.orm import Session

from app.models.checklist import ChecklistItem, ChecklistTemplate, WorkChecklist


def create_work_checklist(
    db: Session,
    service_request_id: int,
    maintenance_mode: str,
    machine_type: str,
):
    template = (
        db.query(ChecklistTemplate)
        .filter(
            ChecklistTemplate.maintenance_mode == maintenance_mode,
            ChecklistTemplate.machine_type == machine_type,
            ChecklistTemplate.is_active.is_(True),
        )
        .order_by(ChecklistTemplate.id.desc())
        .first()
    )

    if template is None:
        return []

    existing = (
        db.query(WorkChecklist)
        .filter(WorkChecklist.service_request_id == service_request_id)
        .count()
    )

    if existing > 0:
        return (
            db.query(WorkChecklist)
            .filter(WorkChecklist.service_request_id == service_request_id)
            .all()
        )

    items = (
        db.query(ChecklistItem)
        .filter(ChecklistItem.template_id == template.id)
        .order_by(ChecklistItem.sequence)
        .all()
    )

    work_items = []

    for item in items:
        work_item = WorkChecklist(
            service_request_id=service_request_id,
            checklist_item_id=item.id,
            completed=False,
        )
        db.add(work_item)
        work_items.append(work_item)

    db.flush()

    return work_items
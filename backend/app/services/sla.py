from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.core.constants import Priority, SLAStatus


@dataclass
class SLAResult:
    deadline: datetime
    estimated_finish: datetime
    status: SLAStatus
    remaining_minutes: float


SLA_WINDOWS_HOURS = {
    Priority.LOW: 72,
    Priority.MEDIUM: 48,
    Priority.HIGH: 24,
    Priority.CRITICAL: 4,
}


def calculate_sla(
    priority: Priority,
    travel_minutes: float,
    job_duration_minutes: float,
    resource_wait_minutes: float,
    current_time: datetime | None = None,
) -> SLAResult:
    if current_time is None:
        current_time = datetime.now(timezone.utc)

    deadline = current_time + timedelta(
        hours=SLA_WINDOWS_HOURS[priority]
    )

    estimated_finish = current_time + timedelta(
        minutes=(
            travel_minutes
            + job_duration_minutes
            + resource_wait_minutes
        )
    )

    remaining_minutes = (
        deadline - estimated_finish
    ).total_seconds() / 60

    if remaining_minutes >= 120:
        status = SLAStatus.GREEN
    elif remaining_minutes >= 0:
        status = SLAStatus.AMBER
    else:
        status = SLAStatus.RED

    return SLAResult(
        deadline=deadline,
        estimated_finish=estimated_finish,
        status=status,
        remaining_minutes=remaining_minutes,
    )
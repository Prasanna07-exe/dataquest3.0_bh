from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ServiceRequestCreate(BaseModel):
    customer_id: int
    site_id: int
    machine_id: int
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    maintenance_mode: str
    priority: str
    requested_start_at: datetime | None = None
    requested_end_at: datetime | None = None


class ServiceRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    request_code: str
    customer_id: int
    site_id: int
    machine_id: int
    title: str
    description: str
    maintenance_mode: str
    priority: str
    state: str
    requested_start_at: datetime | None
    requested_end_at: datetime | None
    created_by: int
    created_at: datetime
    updated_at: datetime
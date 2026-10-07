from pydantic import BaseModel, Field


class WorkLogCreate(BaseModel):
    log_type: str = Field(min_length=1, max_length=50)
    description: str = Field(min_length=1)
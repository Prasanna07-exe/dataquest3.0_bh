from pydantic import BaseModel, Field


class ChecklistComplete(BaseModel):
    notes: str | None = Field(default=None, max_length=1000)
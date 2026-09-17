from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class Status(str, Enum):
    new = "new"
    contacted = "contacted"
    qualified = "qualified"
    won = "won"
    lost = "lost"


class LeadCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    company: str = Field(min_length=1, max_length=100)
    region: str = Field(min_length=1, max_length=100)
    status: Status = Status.new


class LeadOut(LeadCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime

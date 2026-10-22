"""Pydantic shapes for the application tracker API."""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict

Status = Literal["saved", "applied", "interviewing", "offer", "rejected"]


class ApplicationCreate(BaseModel):
    job_title: str
    company: str
    job_url: Optional[str] = None
    status: Status = "saved"


class ApplicationUpdate(BaseModel):
    status: Optional[Status] = None
    applied_at: Optional[datetime] = None


class ApplicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_title: str
    company: str
    job_url: Optional[str] = None
    status: str
    applied_at: Optional[datetime] = None
    last_updated: Optional[datetime] = None
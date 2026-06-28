from pydantic import BaseModel, Field
from typing import Literal
from app.schemas.lead import LeadInput, LeadOutput


class BatchJobRequest(BaseModel):
    leads: list[LeadInput] = Field(
        min_length=1,
        max_length=50,
        description="List of lead URLs to process",
    )

    job_label: str | None = Field(default=None, description="Optiona label for this batch (e.g. 'Saas Singapore June')")


class LeadJobResult(BaseModel):
    url: str
    status: Literal["success", "failed"]
    output: LeadOutput | None = None
    error: str | None = None


class BatchJobResponse(BaseModel):
    job_label: str | None
    total: int
    succeeded: int
    failed: int
    hot_leads: int
    warm_leads: int
    cold_leads: int
    results: list[LeadJobResult]

class SingleLeadResponse(BaseModel):
    status: Literal["success", "failed"]
    output: LeadOutput | None = None
    error: str | None = None


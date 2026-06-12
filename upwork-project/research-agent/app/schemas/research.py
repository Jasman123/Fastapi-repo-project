from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ResearchRequest(BaseModel):
    topic: str = Field(..., min_length=5, max_length=500, description="Research topic or question", examples=["Impact of generative AI on the Indonesian lega industry in 2025"])

class ResearchResponse(BaseModel):
    job_id: str
    topic: str
    status: str
    report_markdown: str
    search_queries: list[str]
    sources_count: int
    elapsed_seconds: float
    created_at: datetime

class ReportListItem(BaseModel):
    job_id: str
    topic: str
    status: str
    sources_count: int
    elapsed_seconds: float
    created_at : datetime


class HealthReponse(BaseModel):
    status: str
    version: str
    db: str
    
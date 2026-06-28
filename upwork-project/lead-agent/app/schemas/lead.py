from pydantic import BaseModel, HttpUrl, Field
from typing import Literal


class LeadInput(BaseModel):
    url: str = Field(description="Company website URL to process")
    custom_context: str | None = Field(default=None, description="Optiona extra context fro email personlisation""(e.g. 'client is in legal sector, focus on compliance')")


class EnrichedLead(BaseModel):
    url: str 
    company_name: str | None = None
    industry: str | None = None
    location: str | None = None
    company_size: str | None = None
    description: str | None = None
    tech_stack: list[str] = Field(default=[])
    pain_points: list[str] = Field(default=[])
    contact_email: str | None = None
    contact_name: str | None = None
    key_signals: list[str] = Field(
        default=[],
        description="Phrases from the site that signal buying intent or fit"
    )
    scrape_succes: bool = True
    scrape_error: str | None = None

class ScoredLead(BaseModel):
    enriched: EnrichedLead
    score: int = Field(ge=0, le=100)
    tier: Literal["hot", "warm", "cold"]
    score_breakdown: dict[str, int] = Field(default={}, description="Which criteria contributed how many points")

class LeadOutput(BaseModel):
    url: str
    company_name: str | None
    industry: str | None
    location: str | None
    company_size: str | None
    contact_email: str | None
    score: int
    tier: Literal["hot", "warm", "cold"]
    score_breakdown: dict[str, int]
    email_subject: str | None = None
    email_body: str | None = None
    alert_sent: bool | None = None
    sheets_row: int | None = None
    db_id: int | None = None
    error: str | None = None
    
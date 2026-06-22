from typing import TypedDict
from app.schemas.lead import EnrichedLead, ScoredLead, LeadOutput, LeadInput

class AgentState(TypedDict):
    lead_input: LeadInput

    raw_text: str
    scrape_error: str | None

    enriched: EnrichedLead | None

    scored: ScoredLead | None

    email_subject: str | None
    email_body: str | None

    output: LeadOutput | None

    pipeline_error: str | None

    
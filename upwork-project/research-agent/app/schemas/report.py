from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class SourceRecord:
    title: str
    url: str
    key_points: list[str]
    relevance_score: float

@dataclass
class ReportRecord:
    job_id: str
    topic: str
    status: str
    report_markdown: str
    search_queries: list[str]
    sources: list[SourceRecord]
    elapsed_seconds: float
    error_message: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    
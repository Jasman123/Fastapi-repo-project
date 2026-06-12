import json
from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class ReportModel(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer,primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)
    topic: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="completed")
    report_markdown: Mapped[str] = mapped_column(Text, nullable=False, default="")
    search_queries_json: Mapped[str] = mapped_column(Text, nullable=False, default=[])
    sources_json: Mapped[str] = mapped_column(Text, nullable=False, default=[])
    sources_count: Mapped[int] =  mapped_column(Integer, nullable=False, default=0)
    elapsed_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    error_message: Mapped[str|None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    
    @property
    def search_queries(self) -> list[str]:
        return json.loads(self.search_queries_json)

    @search_queries.setter
    def search_queries(self, value: list[str]) -> None:
        self.search_queries_json = json.dumps(value)

    @property
    def sources(self) -> list[dict]:
        return json.loads(self.sources_json)

    @sources.setter
    def sources(self, value: list[dict]) -> None:
        self.sources_json = json.dumps(value)

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass

class Note(Base):
    __tablename__ = "notes"


    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    attachment_key: Mapped[str] = mapped_column(String, nullable=True)
    attachment_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    def to_dict(self) -> dict:
        return{
            "id": self.id,
            "title": self.title,
            "body": self.body,
            "attachment_key" : self.attachment_key,
            "attachment_name" : self.attachment_name,
            "created_at" : self.created_at,
            "updated_at" : self.updated_at,
        }







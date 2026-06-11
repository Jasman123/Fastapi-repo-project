import enum
import uuid
from datetime import datetime
from functools import lru_cache

from sqlalchemy import Column, String, Integer, Text, Datetime, Enum, Boolean, create_engine, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship
from app.core.config import get_settings


Base = declarative_base()


class JobStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"

class Document(Base):
    __tablename__ = "documents"

    id = Column(String, )
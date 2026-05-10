from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from database import Base

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)
from sqlalchemy import (
    String,
    ForeignKey,
    DateTime,
)


class TaskResult(BaseModel):
    name: str
    error: Optional[str]
    processing_error: Optional[str]
    records_count: Optional[int]
    execution_time: Optional[float]
    is_ready: bool


class EvidencePostRequest(BaseModel):
    index: str
    relative_file_path: str


class EvidenceResponse(BaseModel):
    evidence_id: str
    index: str
    hostname: str
    domain: Optional[str]
    os: str
    os_version: Optional[str]
    ips: List[str]
    created_at: datetime
    tasks: List[str]


class Evidence(Base):
    __tablename__ = "api_evidences"
    evidence_id: Mapped[String] = mapped_column(String, nullable=False, primary_key=True)
    hostname: Mapped[String] = mapped_column(String, nullable=False)
    domain: Mapped[String] = mapped_column(String, nullable=True)
    index: Mapped[String] = mapped_column(String, nullable=False)
    storage_path: Mapped[String] = mapped_column(String, nullable=False)
    os: Mapped[String] = mapped_column(String, nullable=False)
    os_version: Mapped[String] = mapped_column(String, nullable=True)
    ips: Mapped[String] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    tasks: Mapped[list["Task"]] = relationship(cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "api_tasks"
    task_id: Mapped[str] = mapped_column(String, nullable=False, index=True, unique=True, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    evidence_id: Mapped[str] = mapped_column(String, ForeignKey("api_evidences.evidence_id", ondelete="CASCADE"),
                                             nullable=False, index=True)

import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, String, DateTime, Text, Integer
from backend.db.database import Base


class TaskStatus(str, PyEnum):
    IN_PROGRESS = "in_progress"
    WAITING_APPROVAL = "waiting_approval"
    REVIEW_FAILED = "review_failed"
    APPLIED = "applied"
    CANCELLED = "cancelled"


class TaskStage(str, PyEnum):
    CREATED = "created"
    RESEARCH = "research"
    PLANNING = "planning"
    WRITING = "writing"
    REVIEWING = "reviewing"
    AWAITING_APPROVAL = "awaiting_approval"
    APPLYING = "applying"
    COMPLETE = "complete"


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    service = Column(String, nullable=True)
    task_type = Column(String, default="feature")

    status = Column(String, default=TaskStatus.IN_PROGRESS)
    stage = Column(String, default=TaskStage.CREATED)

    research_findings = Column(Text, nullable=True)
    confidence_score = Column(Integer, nullable=True)
    implementation_plan = Column(Text, nullable=True)
    suggested_code = Column(Text, nullable=True)
    review_findings = Column(Text, nullable=True)
    review_verdict = Column(String, nullable=True)
    suggested_tests = Column(Text, nullable=True)
    git_branch = Column(String, nullable=True)

    revision_count = Column(Integer, default=0)
    uploaded_files = Column(Text, default="[]")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

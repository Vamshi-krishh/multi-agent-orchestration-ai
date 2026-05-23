import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.models.task import Task, TaskStatus, TaskStage

router = APIRouter(prefix="/tasks", tags=["tasks"])

KNOWN_SERVICES = ["kos", "icps", "icms", "iads", "ilps", "igw", "iam", "fpcs", "iotcommon"]


class TaskCreate(BaseModel):
    title: str
    description: str
    service: Optional[str] = None
    task_type: Optional[str] = "feature"


class TaskResponse(BaseModel):
    id: str
    title: str
    description: str
    service: Optional[str]
    task_type: str
    status: str
    stage: str
    research_findings: Optional[str]
    confidence_score: Optional[int]
    implementation_plan: Optional[str]
    suggested_code: Optional[str]
    review_findings: Optional[str]
    review_verdict: Optional[str]
    suggested_tests: Optional[str]
    git_branch: Optional[str]
    revision_count: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


@router.post("", response_model=TaskResponse)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    task = Task(
        title=payload.title,
        description=payload.description,
        service=payload.service,
        task_type=payload.task_type,
        status=TaskStatus.IN_PROGRESS,
        stage=TaskStage.CREATED
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return _to_response(task)


@router.get("", response_model=List[TaskResponse])
def list_tasks(db: Session = Depends(get_db)):
    tasks = db.query(Task).order_by(Task.created_at.desc()).all()
    return [_to_response(t) for t in tasks]


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return _to_response(task)


@router.get("/services/list")
def list_services():
    return {"services": KNOWN_SERVICES}


def _to_response(task: Task) -> dict:
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "service": task.service,
        "task_type": task.task_type or "feature",
        "status": task.status,
        "stage": task.stage,
        "research_findings": task.research_findings,
        "confidence_score": task.confidence_score,
        "implementation_plan": task.implementation_plan,
        "suggested_code": task.suggested_code,
        "review_findings": task.review_findings,
        "review_verdict": task.review_verdict,
        "suggested_tests": task.suggested_tests,
        "git_branch": task.git_branch,
        "revision_count": task.revision_count or 0,
        "created_at": task.created_at.isoformat() if task.created_at else "",
        "updated_at": task.updated_at.isoformat() if task.updated_at else "",
    }

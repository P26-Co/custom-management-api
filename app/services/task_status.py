from sqlalchemy import desc
from sqlalchemy.orm import Session
from typing import Optional

from app.constants import (
    TaskStatusCode,
    TaskType,
)
from app.models import TaskStatus
from app.schemas import FilterRequest, PaginatedTaskStatusResponse, TaskStatusResponse


def get_task_status(db: Session, task_id: str) -> Optional[TaskStatus]:
    return db.query(TaskStatus).filter_by(id=task_id).first()


def create_task_status(db: Session, created_by: str = 'SYSTEM') -> TaskStatus:
    """Creates a new import status entry and returns the task_id."""
    task_entry = TaskStatus(
        task_type=TaskType.ZitadelUserImport,
        status=TaskStatusCode.PENDING,
        created_by=created_by
    )
    db.add(task_entry)
    db.commit()
    db.refresh(task_entry)
    return task_entry


def update_task_status(db: Session, task_id: str, task_status: Optional[str] = None, message: Optional[str] = None):
    """Updates the task status row with relevant information."""
    task_status_entry = get_task_status(db, task_id)
    if not task_status_entry:
        return
    if task_status is not None:
        task_status_entry.status = task_status
    if message is not None:
        task_status_entry.message = message

    db.commit()
    db.refresh(task_status_entry)


def list_task_statuses(db: Session, filters: FilterRequest) -> PaginatedTaskStatusResponse:
    """
    Return a paginated list of ZitadelTenant rows.
    """
    query = db.query(TaskStatus)
    total = query.count()
    items = (
        query
        .order_by(desc(TaskStatus.created_at))
        .offset((filters.page - 1) * filters.size)
        .limit(filters.size)
        .all()
    )

    return PaginatedTaskStatusResponse(
        total=total,
        page=filters.page,
        size=filters.size,
        items=[
            TaskStatusResponse(
                id=str(u.id),
                status=str(u.status),  # type: ignore
                message=str(u.message) if u.message else None,
                task_type=str(u.task_type),  # type: ignore
                created_at=u.created_at  # type: ignore
            )
            for u in items
        ]
    )

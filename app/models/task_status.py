from sqlalchemy import (
    Column,
    String,
)

from app.constants import TaskStatusCode, TaskType
from app.database import Base
from app.models.audit import AuditColumnsMixin


class TaskStatus(Base, AuditColumnsMixin):
    __tablename__ = "task_status"

    status = Column(String(255), default=TaskStatusCode.PENDING)  # e.g. PENDING, IN_PROGRESS, COMPLETED, FAILED
    task_type = Column(String(255), nullable=False, default=TaskType.ZitadelUserImport)
    message = Column(String(255), nullable=True)

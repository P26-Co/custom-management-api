from datetime import datetime

from pydantic import BaseModel
from typing import Optional, List

from app.constants import TaskStatusCode, TaskType
from app.schemas import PaginatedResponse


class TaskStatusResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    status: TaskStatusCode
    task_type: TaskType
    message: Optional[str]
    created_at: Optional[datetime] = None


class PaginatedTaskStatusResponse(PaginatedResponse):
    items: List[TaskStatusResponse]

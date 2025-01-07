from fastapi import Depends, BackgroundTasks, HTTPException, APIRouter, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.constants import ErrorMessage
from app.database import get_db
from app.services.tasks import import_zitadel_users
from app.utils import decode_access_token
from app.schemas import (
    TaskStatusResponse,
    FilterRequest,
    PaginatedTaskStatusResponse,
)
from app.services.task_status import (
    create_task_status,
    get_task_status, list_task_statuses
)

# Create the Bearer security scheme
bearer_scheme = HTTPBearer()

router = APIRouter()


@router.post("/zitadel-import-users", response_model=TaskStatusResponse)
def trigger_import(
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_db),
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    token = decode_access_token(credentials.credentials, only_admin=True)

    # Step 1: Create an import task status record
    task = create_task_status(db, token.id)

    # Step 2: Add a background task to import users
    background_tasks.add_task(import_zitadel_users, db, task.id)

    # Step 3: Return the task_id so the client can check the status
    return TaskStatusResponse(
        id=task.id,
        status=task.status,  # type: ignore
        task_type=task.task_type,  # type: ignore
        message=task.message,
        created_at=task.created_at  # type: ignore
    )


@router.get("/{task_id}", response_model=TaskStatusResponse)
def check_import_status(
        task_id: str,
        db: Session = Depends(get_db),
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    decode_access_token(credentials.credentials, only_admin=True)

    status_entry = get_task_status(db, task_id)
    if not status_entry:
        raise HTTPException(status_code=404, detail=ErrorMessage.TASK_STATUS_NOT_FOUND)

    return TaskStatusResponse(
        id=status_entry.id,
        status=status_entry.status,  # type: ignore
        task_type=status_entry.task_type,  # type: ignore
        message=status_entry.message
    )


@router.get("/", response_model=PaginatedTaskStatusResponse)
def get_task_statuses(
        page: int = Query(1),
        size: int = Query(10),
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
        db: Session = Depends(get_db),
):
    decode_access_token(credentials.credentials, only_admin=True)
    return list_task_statuses(
        db,
        FilterRequest(
            page=page,
            size=size
        )
    )

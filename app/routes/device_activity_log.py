from fastapi import Depends, Query, APIRouter
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.utils import decode_access_token
from app.schemas import (
    ListDeviceLogsFilters,
    PaginatedDeviceLogsResponse,
)
from app.services.device_activity_log import list_device_logs

# Create the Bearer security scheme
bearer_scheme = HTTPBearer()

router = APIRouter()


@router.get("/", response_model=PaginatedDeviceLogsResponse)
def get_device_logs(
        tenant_id: str = Query(None),
        zitadel_user_id: str = Query(None),
        device_id: str = Query(None),
        device_user_id: str = Query(None),
        page: int = Query(1),
        size: int = Query(10),
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
        db: Session = Depends(get_db),
):
    token = decode_access_token(credentials.credentials, admin_or_manager=True)
    return list_device_logs(
        db,
        ListDeviceLogsFilters(
            tenantId=token.tenant_id if token.tenant_id else tenant_id,
            zitadelUserId=zitadel_user_id,
            deviceId=device_id,
            deviceUserId=device_user_id,
            page=page,
            size=size
        )
    )

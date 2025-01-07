from fastapi import Depends, Query, Path, APIRouter
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    GenericMessageResponse,
    ListDeviceUsersFilters,
    PaginatedDeviceUserResponse,
)
from app.services.device_user import (
    list_device_users,
    delete_device_user,
)
from app.utils import decode_access_token

# Create the Bearer security scheme
bearer_scheme = HTTPBearer()

router = APIRouter()


@router.get("/", response_model=PaginatedDeviceUserResponse)
def get_device_users(
        tenant_id: str = Query(None),
        zitadel_user_id: str = Query(None),
        device_id: str = Query(None),
        page: int = Query(1),
        size: int = Query(10),
        db: Session = Depends(get_db),
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    token = decode_access_token(credentials.credentials, admin_or_manager=True)
    return list_device_users(
        db,
        ListDeviceUsersFilters(
            tenantId=token.tenant_id if token.tenant_id else tenant_id,
            zitadelUserId=zitadel_user_id if zitadel_user_id else None,
            deviceId=device_id if device_id else None,
            page=page,
            size=size
        )
    )


@router.delete("/{device_user_id}", response_model=GenericMessageResponse)
def delete_device_user_api(
        device_user_id: str = Path(...),
        db: Session = Depends(get_db),
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    """
    Delete a device user by ID.
    """
    token = decode_access_token(credentials.credentials, admin_or_manager=True)
    return delete_device_user(db, device_user_id, token.id)

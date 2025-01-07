from fastapi import Depends, Query, APIRouter
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    GenericMessageResponse,
    SharedUserCreateRequest,
    ListSharedUsersFilters,
    PaginatedSharedUserResponse,
)
from app.services.shared_user import (
    share_device_user,
    remove_shared_user,
    list_shared_users,
)
from app.utils import decode_access_token

# Create the Bearer security scheme
bearer_scheme = HTTPBearer()

router = APIRouter()


@router.post("/")
def share_device_user_api(
        payload: SharedUserCreateRequest,
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
        db: Session = Depends(get_db)
):
    """
    7. API: POST /shared-user
    Req: deviceId, deviceUserId, zitadelUserId
    Res: The created SharedUser object
    """
    token = decode_access_token(credentials.credentials, admin_or_manager=True)
    return share_device_user(db, token.id, payload)


@router.delete("/{shared_user_id}", response_model=GenericMessageResponse)
def remove_shared_user_api(
        shared_user_id: str,
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
        db: Session = Depends(get_db)
):
    """
    8. API: DELETE /shared-user
    Req: sharedUserId
    Res: success message
    """
    token = decode_access_token(credentials.credentials, admin_or_manager=True)
    return remove_shared_user(db, token.id, shared_user_id)


@router.get("/", response_model=PaginatedSharedUserResponse)
def get_shared_users(
        tenant_id: str = Query(None),
        zitadel_user_id: str = Query(None),
        device_user_id: str = Query(None),
        page: int = Query(1),
        size: int = Query(10),
        db: Session = Depends(get_db),
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    token = decode_access_token(credentials.credentials, admin_or_manager=True)
    return list_shared_users(
        db,
        ListSharedUsersFilters(
            tenantId=token.tenant_id if token.tenant_id else tenant_id,
            zitadelUserId=zitadel_user_id if zitadel_user_id != 0 else None,
            deviceUserId=device_user_id if device_user_id != 0 else None,
            page=page,
            size=size
        )
    )

from fastapi import Depends, Query, Path, APIRouter
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    GenericMessageResponse,
    ListDevicesFilters,
    DeviceSchema,
    PaginatedDeviceResponse,
)
from app.services.device import (
    list_devices,
    update_device,
    delete_device,
)
from app.utils import decode_access_token

# Create the Bearer security scheme
bearer_scheme = HTTPBearer()

router = APIRouter()


@router.get("/", response_model=PaginatedDeviceResponse)
def get_devices(
        tenant_id: str = Query(None),
        zitadel_user_id: str = Query(None),
        page: int = Query(1),
        size: int = Query(10),
        db: Session = Depends(get_db),
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    token = decode_access_token(credentials.credentials, admin_or_manager=True)
    return list_devices(
        db,
        ListDevicesFilters(
            tenantId=token.tenant_id if token.tenant_id else tenant_id,
            zitadelUserId=zitadel_user_id if zitadel_user_id else None,
            page=page,
            size=size
        )
    )


@router.patch("/{device_id}", response_model=DeviceSchema)
def update_device_api(
        payload: DeviceSchema,
        db: Session = Depends(get_db),
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    """
    Update an existing device.
    """
    token = decode_access_token(credentials.credentials, admin_or_manager=True)
    return update_device(db, payload, token.id)


@router.delete("/{device_id}", response_model=GenericMessageResponse)
def delete_device_api(
        device_id: str = Path(...),
        db: Session = Depends(get_db),
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    """
    Delete a device by ID.
    """
    token = decode_access_token(credentials.credentials, admin_or_manager=True)
    return delete_device(db, device_id, token.id)

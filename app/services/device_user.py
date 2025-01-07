from sqlalchemy import desc
from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import Type

from app.constants import (
    PortalActivityAction,
    ErrorMessage,
    SuccessMessage,
)
from app.models import (
    ZitadelUser,
    SharedUser,
    DeviceUser,
)
from app.schemas import (
    DeviceSchema,
    ListDeviceUsersFilters,
    DeviceUserSchema,
    PaginatedDeviceUserResponse,
    GenericMessageResponse,
    ZitadelUserSchema
)
from app.services.portal_activity_log import log_portal_activity


def get_device_user_by_username(db: Session, device_username: str) -> Type[DeviceUser] | None:
    return db.query(DeviceUser).filter(DeviceUser.device_username == device_username).first()


def get_device_user_by_id(db: Session, device_user_id: str) -> Type[DeviceUser] | None:
    return db.query(DeviceUser).filter(DeviceUser.id == device_user_id).first()


def list_device_users(db: Session, filters: ListDeviceUsersFilters) -> PaginatedDeviceUserResponse:
    """
    Return a paginated list of DeviceUser rows, optionally filtered by tenant, user, device.
    """
    query = db.query(DeviceUser)

    if filters.tenantId:
        # join device_users -> zitadel_user => match tenant
        query = query.join(ZitadelUser).filter(ZitadelUser.tenant_id == filters.tenantId)

    if filters.zitadelUserId:
        query = query.filter(DeviceUser.zitadel_user_id == filters.zitadelUserId)

    if filters.deviceId:
        query = query.filter(DeviceUser.device_id == filters.deviceId)

    total = query.count()
    items = (
        query
        .order_by(desc(DeviceUser.created_at))
        .offset((filters.page - 1) * filters.size)
        .limit(filters.size)
        .all()
    )

    return PaginatedDeviceUserResponse(
        total=total,
        page=filters.page,
        size=filters.size,
        items=[
            DeviceUserSchema(
                id=str(d.id),
                device_username=str(d.device_username),
                user=ZitadelUserSchema(
                    id=str(d.zitadel_user_id),
                    name=d.zitadel_user.name,
                    email=d.zitadel_user.email,
                    tenant_id=d.zitadel_user.tenant_id
                ),
                device=DeviceSchema(
                    id=str(d.device_id),
                    name=d.device.name,
                    device_id=d.device.device_id
                )
            )
            for d in items
        ]
    )


def delete_device_user(db: Session, device_user_id: str, portal_user_id: str) -> GenericMessageResponse:
    shared_users = db.query(SharedUser).filter(SharedUser.device_user_id == device_user_id).all()
    for shared_user in shared_users:
        db.delete(shared_user)

    device = get_device_user_by_id(db, device_user_id)
    if not device:
        raise HTTPException(status_code=404, detail=ErrorMessage.DEVICE_USER_NOT_FOUND)
    db.delete(device)

    log_portal_activity(
        db,
        portal_user_id=portal_user_id,
        endpoint="/device-users",
        action=PortalActivityAction.DELETE,
        device_user_id=device_user_id,
        device_id=device.device_id,  # type: ignore
        zitadel_user_id=device.zitadel_user_id  # type: ignore
    )
    db.commit()

    return GenericMessageResponse(message=SuccessMessage.USER_REMOVED)

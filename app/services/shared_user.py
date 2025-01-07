from sqlalchemy import desc
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.constants import (
    PortalActivityAction,
    ErrorMessage,
    SuccessMessage,
)
from app.models import (
    ZitadelUser,
    SharedUser,
    DeviceUser,
    Device,
)
from app.schemas import (
    DeviceSchema,
    DeviceUserSchema,
    GenericMessageResponse,
    SharedUserCreateRequest,
    ListSharedUsersFilters,
    SharedUserSchema,
    PaginatedSharedUserResponse,
    ZitadelUserSchema
)
from app.services.portal_activity_log import log_portal_activity


def share_device_user(db: Session, portal_user_id: str, payload: SharedUserCreateRequest) -> SharedUser:
    """
    Creates a SharedUser entry, effectively sharing a deviceUser with a specified Zitadel user.
    """
    exist_record = db.query(SharedUser).filter(
        SharedUser.device_user_id == payload.deviceUserId,
        SharedUser.shared_with_user_id == payload.zitadelUserId
    ).first()
    if exist_record:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=ErrorMessage.SHARED_USER_EXISTS)

    device = db.query(Device).filter(Device.id == payload.deviceId).first()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ErrorMessage.DEVICE_NOT_FOUND)

    device_user = db.query(DeviceUser).filter(DeviceUser.id == payload.deviceUserId).first()
    if not device_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ErrorMessage.DEVICE_USER_NOT_FOUND)

    to_share_user = db.query(ZitadelUser).filter(ZitadelUser.id == payload.zitadelUserId).first()
    if not to_share_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ErrorMessage.USER_NOT_FOUND)

    new_shared = SharedUser(
        device_user_id=str(device_user.id),
        shared_with_user_id=str(to_share_user.id),
        created_by=portal_user_id,
    )
    db.add(new_shared)
    db.commit()
    db.refresh(new_shared)

    log_portal_activity(
        db,
        portal_user_id=portal_user_id,
        endpoint="/shared-user",
        action=PortalActivityAction.CREATE,
        shared_user_id=new_shared.id,
        zitadel_user_id=str(to_share_user.id),
        device_user_id=str(device_user.id)
    )

    return new_shared


def remove_shared_user(db: Session, portal_user_id: str, shared_user_id: str) -> GenericMessageResponse:
    """
    Deletes a SharedUser entry by its primary key.
    """
    shared_to_remove = db.query(SharedUser).filter(SharedUser.id == shared_user_id).first()
    if not shared_to_remove:
        raise HTTPException(status_code=404, detail=ErrorMessage.SHARED_USER_NOT_FOUND)

    db.delete(shared_to_remove)

    log_portal_activity(
        db,
        portal_user_id=portal_user_id,
        endpoint="/shared-user",
        action=PortalActivityAction.DELETE,
        shared_user_id=shared_user_id,
        zitadel_user_id=str(shared_to_remove.shared_with_user_id),
        device_user_id=str(shared_to_remove.device_user_id)
    )
    db.commit()

    return GenericMessageResponse(message=SuccessMessage.SHARED_USER_REMOVED)


def list_shared_users(db: Session, filters: ListSharedUsersFilters) -> PaginatedSharedUserResponse:
    """
    Return a paginated list of SharedUser rows, optionally filtered by tenant, user, device, deviceUserId.
    """
    query = db.query(SharedUser)

    # If tenantId is provided, we must join through device -> device_users -> zitadel_user => tenant_id
    if filters.tenantId:
        query = query.join(
            DeviceUser, (DeviceUser.id == SharedUser.device_user_id)
        ).join(
            ZitadelUser, DeviceUser.zitadel_user_id == ZitadelUser.id
        ).filter(
            ZitadelUser.tenant_id == filters.tenantId
        )

    if filters.zitadelUserId:
        query = query.filter(SharedUser.shared_with_user_id == filters.zitadelUserId)

    if filters.deviceUserId:
        query = query.join(
            DeviceUser, DeviceUser.id == SharedUser.device_user_id
        ).filter(
            DeviceUser.id == filters.deviceUserId
        )

    query = query.distinct()
    total = query.count()
    items = (
        query
        .order_by(desc(SharedUser.created_at))
        .offset((filters.page - 1) * filters.size)
        .limit(filters.size)
        .all()
    )

    return PaginatedSharedUserResponse(
        total=total,
        page=filters.page,
        size=filters.size,
        items=[
            SharedUserSchema(
                id=str(d.id),
                device_user=DeviceUserSchema(
                    id=str(d.device_user_id),
                    device_username=d.device_user.device_username,
                    user=ZitadelUserSchema(
                        id=d.device_user.zitadel_user_id,
                        name=d.device_user.zitadel_user.name,
                        email=d.device_user.zitadel_user.email
                    ),
                ),
                device=DeviceSchema(
                    id=d.device_user.device.id,
                    device_id=d.device_user.device.device_id,
                    name=d.device_user.device.name
                ),
                user=ZitadelUserSchema(
                    id=str(d.shared_with_user_id),
                    name=d.shared_with_user.name,
                    email=d.shared_with_user.email
                )
            )
            for d in items
        ]
    )

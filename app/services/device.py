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
    Device,
)
from app.schemas import (
    ListDevicesFilters,
    DeviceSchema,
    PaginatedDeviceResponse,
    GenericMessageResponse
)
from app.services.portal_activity_log import log_portal_activity


def get_device_by_device_id(db: Session, device_id: str) -> Type[Device] | None:
    return db.query(Device).filter(Device.device_id == device_id).first()


def get_device_by_id(db: Session, device_id: str) -> Type[Device] | None:
    return db.query(Device).filter(Device.id == device_id).first()


def create_device_if_not_exists(db: Session, device_id: str, name: str, user_id: str = None) -> Device:
    device = get_device_by_device_id(db, device_id)
    if not device:
        device = Device(
            device_id=device_id,
            name=name,
            zitadel_user_id=user_id,
            created_by=user_id
        )
        db.add(device)
        db.commit()
        db.refresh(device)
    return device


def list_devices(db: Session, filters: ListDevicesFilters) -> PaginatedDeviceResponse:
    """
    Return a paginated list of Devices, optionally filtered by tenant, user.
    """
    query = db.query(Device)

    if filters.tenantId:
        query = query.join(ZitadelUser).filter(
            ZitadelUser.tenant_id == filters.tenantId
        )

    if filters.zitadelUserId:
        query = query.filter(Device.zitadel_user_id == filters.zitadelUserId)

    query = query.distinct()
    total = query.count()
    items = (
        query
        .order_by(desc(Device.created_at))
        .offset((filters.page - 1) * filters.size)
        .limit(filters.size)
        .all()
    )

    return PaginatedDeviceResponse(
        total=total,
        page=filters.page,
        size=filters.size,
        items=[
            DeviceSchema(
                id=str(d.id),
                device_id=str(d.device_id),
                name=str(d.name) if d.name else None,
                len_device_users=len(d.device_users) if d.device_users else 0,
            )
            for d in items
        ]
    )


def update_device(db: Session, payload: DeviceSchema, portal_user_id: str) -> DeviceSchema:
    device = get_device_by_id(db, payload.id)
    if not device:
        raise HTTPException(status_code=404, detail=ErrorMessage.DEVICE_NOT_FOUND)

    if payload.name is not None:
        device.name = payload.name

    db.commit()
    db.refresh(device)

    log_portal_activity(
        db,
        portal_user_id=portal_user_id,
        endpoint="/devices",
        action=PortalActivityAction.UPDATE,
        device_id=str(device.id)
    )

    return DeviceSchema(
        id=str(device.id),
        device_id=str(device.device_id),
        name=str(device.name),
    )


def delete_device(db: Session, device_id: str, portal_user_id: str) -> GenericMessageResponse:
    device_users = db.query(DeviceUser).filter(DeviceUser.device_id == device_id).all()
    for device_user in device_users:
        shared_users = db.query(SharedUser).filter(SharedUser.device_user_id == device_user.id).all()
        for shared_user in shared_users:
            db.delete(shared_user)
        db.delete(device_user)

    device = get_device_by_id(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail=ErrorMessage.DEVICE_NOT_FOUND)
    db.delete(device)

    log_portal_activity(
        db,
        portal_user_id=portal_user_id,
        endpoint="/devices",
        action=PortalActivityAction.DELETE,
        device_id=device_id
    )
    db.commit()

    return GenericMessageResponse(message=SuccessMessage.USER_REMOVED)

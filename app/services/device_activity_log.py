from sqlalchemy import desc
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.constants import (
    DeviceActivityType,
    ErrorMessage,
)
from app.models import (
    ZitadelUser,
    DeviceActivityLog,
)
from app.schemas import (
    TokenResponse,
    DeviceSchema,
    ListDeviceLogsFilters,
    DeviceLogsSchema,
    PaginatedDeviceLogsResponse,
    DeviceUserSchema,
    ZitadelUserSchema,
    TokenData
)
from app.services.device import get_device_by_device_id
from app.services.device_user import get_device_user_by_username
from app.utils import create_access_token


def create_device_log(
        db: Session,
        user_id: str,
        device_id: str,
        device_username: str,
        login_as: str = None,
        activity_type: str = DeviceActivityType.device_login
):
    activity = DeviceActivityLog(
        zitadel_user_id=user_id,
        device_id=device_id,
        device_username=device_username,
        login_as=login_as,
        activity_type=activity_type,
        created_by=user_id
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


def add_device_log(
        db: Session,
        user_id: str,
        login_as: str,
        device_id: str,
        device_username: str,
        activity_type: str = DeviceActivityType.device_login
) -> TokenResponse:
    user = db.query(ZitadelUser).filter(ZitadelUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=ErrorMessage.USER_NOT_FOUND)

    device = get_device_by_device_id(db, device_id)
    if not device:
        raise HTTPException(status_code=400, detail=ErrorMessage.DEVICE_NOT_FOUND)

    device_user = get_device_user_by_username(db, device_username)
    if not device:
        raise HTTPException(status_code=400, detail=ErrorMessage.DEVICE_USER_NOT_FOUND)

    # log activity
    create_device_log(
        db,
        str(user.id),
        str(device.id),
        str(device_user.id),
        login_as=login_as,
        activity_type=activity_type
    )

    # return token
    return TokenResponse(token=create_access_token(TokenData(id=user.id, email=user.email)))  # type: ignore


def list_device_logs(db: Session, filters: ListDeviceLogsFilters) -> PaginatedDeviceLogsResponse:
    query = db.query(DeviceActivityLog)
    if filters.tenantId:
        query = query.join(ZitadelUser).filter(ZitadelUser.tenant_id == filters.tenantId)

    if filters.zitadelUserId:
        query = query.filter(DeviceActivityLog.zitadel_user_id == filters.zitadelUserId)

    if filters.deviceId:
        query = query.filter(DeviceActivityLog.device_id == filters.deviceId)

    if filters.deviceUserId:
        query = query.filter(DeviceActivityLog.device_username == filters.deviceUserId)

    total = query.count()
    items = (
        query
        .order_by(desc(DeviceActivityLog.created_at))
        .offset((filters.page - 1) * filters.size)
        .limit(filters.size)
        .all()
    )

    return PaginatedDeviceLogsResponse(
        total=total,
        page=filters.page,
        size=filters.size,
        items=[
            DeviceLogsSchema(
                id=str(d.id),
                timestamp=str(d.timestamp),
                activity_type=str(d.activity_type),
                login_as=str(d.login_as) if d.login_as else None,
                device_user=DeviceUserSchema(
                    id=str(d.device_username),
                    device_username=d.device_user.device_username,
                    user=ZitadelUserSchema(
                        id=d.device_user.zitadel_user_id,
                        name=d.device_user.zitadel_user.name,
                        email=d.device_user.zitadel_user.email
                    ) if d.device_user.zitadel_user else None,
                ) if d.device_user else None,
                user=ZitadelUserSchema(
                    id=str(d.zitadel_user_id),
                    name=d.zitadel_user.name,
                    email=d.zitadel_user.email
                ) if d.zitadel_user else None,
                device=DeviceSchema(
                    id=str(d.device_id),
                    name=d.device.name,
                    device_id=d.device.device_id
                ) if d.device else None
            )
            for d in items
        ]
    )

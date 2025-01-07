from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models import (
    ZitadelUser,
    PortalActivityLog,
)
from app.schemas import (
    ListPortalLogsFilters,
    PaginatedPortalLogsResponse,
    PortalLogsSchema,
    PortalUserResponse,
    DeviceSchema,
    DeviceUserSchema,
    SharedUserSchema,
    ZitadelUserSchema
)


def log_portal_activity(
        db: Session,
        portal_user_id: str,
        endpoint: str,
        action: str = "",
        zitadel_user_id: str = None,
        zitadel_tenant_id: str = None,
        device_id: str = None,
        device_user_id: str = None,
        shared_user_id: str = None
) -> None:
    """
    Insert a row in portal_activity_logs to track usage.
    """
    entry = PortalActivityLog(
        portal_user_id=portal_user_id,
        endpoint=endpoint,
        action=action,
        zitadel_user_id=zitadel_user_id,
        zitadel_tenant_id=zitadel_tenant_id,
        device_id=device_id,
        device_user_id=device_user_id,
        shared_user_id=shared_user_id,
        created_by=portal_user_id
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)


def list_portal_logs(db: Session, filters: ListPortalLogsFilters) -> PaginatedPortalLogsResponse:
    query = db.query(PortalActivityLog)
    if filters.tenantId:
        query = query.join(ZitadelUser).filter(ZitadelUser.tenant_id == filters.tenantId)

    if filters.portalUserId:
        query = query.filter(PortalActivityLog.portal_user_id == filters.portalUserId)

    if filters.zitadelUserId:
        query = query.filter(PortalActivityLog.zitadel_user_id == filters.zitadelUserId)

    if filters.deviceId:
        query = query.filter(PortalActivityLog.device_id == filters.deviceId)

    if filters.deviceUserId:
        query = query.filter(PortalActivityLog.device_user_id == filters.deviceUserId)

    if filters.sharedUserId:
        query = query.filter(PortalActivityLog.shared_user_id == filters.sharedUserId)

    total = query.count()
    items = (
        query
        .order_by(desc(PortalActivityLog.created_at))
        .offset((filters.page - 1) * filters.size)
        .limit(filters.size)
        .all()
    )

    return PaginatedPortalLogsResponse(
        total=total,
        page=filters.page,
        size=filters.size,
        items=[
            PortalLogsSchema(
                id=str(d.id),
                timestamp=str(d.timestamp),
                endpoint=str(d.endpoint),
                action=str(d.action) if d.action else None,
                portal_user=PortalUserResponse.model_validate(d.portal_user) if d.portal_user else None,
                device_user=DeviceUserSchema(
                    id=str(d.device_user_id),
                    device_username=d.device_user.device_username if d.device_user else None,
                    user=ZitadelUserSchema(
                        id=d.device_user.zitadel_user_id,
                        name=d.device_user.zitadel_user.name,
                        email=d.device_user.zitadel_user.email
                    ) if d.device_user else None,
                ) if d.device_user_id else None,
                user=ZitadelUserSchema(
                    id=str(d.zitadel_user_id),
                    name=d.zitadel_user.name if d.zitadel_user else None,
                    email=d.zitadel_user.email if d.zitadel_user else None
                ) if d.zitadel_user_id else None,
                device=DeviceSchema(
                    id=str(d.device_id),
                    name=d.device.name if d.device else None,
                    device_id=d.device.device_id if d.device else None
                ) if d.device_id else None,
                shared_user=SharedUserSchema(
                    id=str(d.shared_user_id),
                    user=ZitadelUserSchema(
                        id=d.shared_user.shared_with_user_id,
                        name=d.shared_user.shared_with_user.name,
                        email=d.shared_user.shared_with_user.email
                    ) if d.shared_user else None,
                    device=DeviceSchema(
                        id=d.shared_user.device_user.device_id,
                        name=d.shared_user.device_user.device.name,
                        device_id=d.shared_user.device_user.device.device_id
                    ) if d.shared_user else None,
                    device_user=DeviceUserSchema(
                        id=d.shared_user.device_user_id,
                        device_username=d.shared_user.device_user.device_username,
                        user=ZitadelUserSchema(
                            id=d.shared_user.device_user.zitadel_user_id,
                            name=d.shared_user.device_user.zitadel_user.name,
                            email=d.shared_user.device_user.zitadel_user.email
                        )
                    ) if d.shared_user else None
                ) if d.shared_user_id else None
            )
            for d in items
        ]
    )

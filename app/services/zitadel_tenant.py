from fastapi import HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session
from typing import Type

from app.constants import (
    PortalActivityAction,
    SuccessMessage,
    ErrorMessage
)
from app.models import (
    ZitadelTenant,
    ZitadelUser,
    SharedUser,
    DeviceUser,
    Device
)
from app.schemas import (
    ZitadelTenantSchema,
    FilterRequest,
    PaginatedZitadelTenantResponse,
    GenericMessageResponse
)
from app.services.portal_activity_log import log_portal_activity


def get_zitadel_tenant_by_id(db: Session, zitadel_tenant_id: str) -> Type[ZitadelTenant]:
    return db.query(ZitadelTenant).filter(ZitadelTenant.id == zitadel_tenant_id).first()


def get_zitadel_tenant_by_zitadel_tenant_id(db: Session, zitadel_tenant_id: str) -> Type[ZitadelTenant]:
    return db.query(ZitadelTenant).filter_by(zitadel_tenant_id=zitadel_tenant_id).first()


def create_zitadel_tenant(db: Session, data: ZitadelTenantSchema) -> ZitadelTenant | Type[ZitadelTenant]:
    """
    Creates a single ZitadelTenant if it doesn't exist yet.
    """
    existing = get_zitadel_tenant_by_zitadel_tenant_id(db, data.zitadel_tenant_id)
    if not existing:
        new_tenant = ZitadelTenant(
            zitadel_tenant_id=data.zitadel_tenant_id,
            name=data.name,
            created_by='SYSTEM'
        )
        db.add(new_tenant)
        db.commit()
        db.refresh(new_tenant)
        return new_tenant
    return existing


def list_zitadel_tenants(db: Session, filters: FilterRequest) -> PaginatedZitadelTenantResponse:
    """
    Return a paginated list of ZitadelTenant rows.
    """
    query = db.query(ZitadelTenant)
    total = query.count()
    items = (
        query
        .order_by(desc(ZitadelTenant.created_at))
        .offset((filters.page - 1) * filters.size)
        .limit(filters.size)
        .all()
    )

    return PaginatedZitadelTenantResponse(
        total=total,
        page=filters.page,
        size=filters.size,
        items=[
            ZitadelTenantSchema(
                id=str(u.id),
                name=str(u.name) if u.name else None,
                zitadel_tenant_id=str(u.zitadel_tenant_id)
            )
            for u in items
        ]
    )


def delete_zitadel_tenant(db: Session, zitadel_tenant_id: str, portal_user_id: str) -> GenericMessageResponse:
    zitadel_tenant = get_zitadel_tenant_by_id(db, zitadel_tenant_id)
    if not zitadel_tenant:
        raise HTTPException(status_code=404, detail=ErrorMessage.TENANT_NOT_FOUND)

    zitadel_users = db.query(ZitadelUser).filter(ZitadelUser.tenant_id == zitadel_tenant_id).all()
    for zitadel_user in zitadel_users:

        shared_users = db.query(SharedUser).filter(SharedUser.shared_with_user_id == zitadel_user.id).all()
        for shared_user in shared_users:
            db.delete(shared_user)

        device_users = db.query(DeviceUser).filter(DeviceUser.zitadel_user_id == zitadel_user.id).all()
        for device_user in device_users:

            shared_users = db.query(SharedUser).filter(SharedUser.device_user_id == device_user.id).all()
            for shared_user in shared_users:
                db.delete(shared_user)

            db.delete(device_user)

        devices = db.query(Device).filter(Device.zitadel_user_id == zitadel_user.id).all()
        for device in devices:
            db.delete(device)

        db.delete(zitadel_user)

    db.delete(zitadel_tenant)

    log_portal_activity(
        db,
        portal_user_id=portal_user_id,
        endpoint="/zitadel-tenants",
        action=PortalActivityAction.DELETE,
        zitadel_tenant_id=zitadel_tenant_id
    )
    db.commit()

    return GenericMessageResponse(message=SuccessMessage.TENANT_REMOVED)

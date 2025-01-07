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
    GenericMessageResponse,
    ZitadelTenantSchema,
    ListZitadelUsersFilters,
    ZitadelUserSchema,
    PaginatedZitadelUserResponse
)
from app.services.portal_activity_log import log_portal_activity


def get_zitadel_user_by_id(db: Session, zitadel_user_id: str) -> Type[ZitadelUser]:
    return db.query(ZitadelUser).filter(ZitadelUser.id == zitadel_user_id).first()


def get_zitadel_user_by_zitadel_user_id(db: Session, zitadel_user_id: str) -> Type[ZitadelUser]:
    return db.query(ZitadelUser).filter_by(zitadel_user_id=zitadel_user_id).first()


def create_zitadel_user(db: Session, user: ZitadelUserSchema) -> ZitadelUser | Type[ZitadelUser]:
    """
    Creates a single ZitadelUser if it doesn't exist yet.
    """
    existing_user = get_zitadel_user_by_zitadel_user_id(db, user.zitadel_user_id)
    if not existing_user:
        new_user = ZitadelUser(
            zitadel_user_id=user.zitadel_user_id,
            tenant_id=user.tenant_id,
            email=user.email,
            name=user.name,
            created_by='SYSTEM'
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    return existing_user


def list_zitadel_users(db: Session, filters: ListZitadelUsersFilters) -> PaginatedZitadelUserResponse:
    """
    Return a paginated list of ZitadelUser rows, optionally filtered by tenant_id.
    """
    query = db.query(ZitadelUser)
    if filters.tenantId:
        query = query.filter(ZitadelUser.tenant_id == filters.tenantId)

    total = query.count()
    items = (
        query
        .order_by(desc(ZitadelUser.created_at))
        .offset((filters.page - 1) * filters.size)
        .limit(filters.size)
        .all()
    )

    return PaginatedZitadelUserResponse(
        total=total,
        page=filters.page,
        size=filters.size,
        items=[
            ZitadelUserSchema(
                id=str(u.id),
                email=str(u.email),
                name=str(u.name),
                tenant_id=str(u.tenant_id),
                zitadel_user_id=str(u.zitadel_user_id),
                tenant=ZitadelTenantSchema(
                    id=str(u.tenant_id),
                    name=u.tenant.name,
                    zitadel_tenant_id=u.tenant.zitadel_tenant_id
                ) if u.tenant else None
            )
            for u in items
        ]
    )


def delete_zitadel_user(db: Session, zitadel_user_id: str, portal_user_id: str) -> GenericMessageResponse:
    shared_users = db.query(SharedUser).filter(SharedUser.shared_with_user_id == zitadel_user_id).all()
    for shared_user in shared_users:
        db.delete(shared_user)

    device_users = db.query(DeviceUser).filter(DeviceUser.zitadel_user_id == zitadel_user_id).all()
    for device_user in device_users:
        shared_users = db.query(SharedUser).filter(SharedUser.device_user_id == device_user.id).all()
        for shared_user in shared_users:
            db.delete(shared_user)
        db.delete(device_user)

    zitadel_user = get_zitadel_user_by_id(db, zitadel_user_id)
    if not zitadel_user:
        raise HTTPException(status_code=404, detail=ErrorMessage.USER_NOT_FOUND)

    db.delete(zitadel_user)

    log_portal_activity(
        db,
        portal_user_id=portal_user_id,
        endpoint="/zitadel-users",
        action=PortalActivityAction.DELETE,
        zitadel_user_id=zitadel_user_id
    )
    db.commit()

    return GenericMessageResponse(message=SuccessMessage.USER_REMOVED)

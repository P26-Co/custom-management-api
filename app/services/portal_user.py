from sqlalchemy import desc
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import Type

from app.constants import (
    PortalActivityAction,
    ErrorMessage,
    SuccessMessage,
)
from app.models import PortalUser, ZitadelTenant
from app.schemas import (
    ListPortalUsersFilters,
    PortalUserCreateRequest,
    PortalUserResponse,
    PortalUserUpdateRequest,
    PortalTokenResponse,
    PaginatedPortalUserResponse,
    GenericMessageResponse,
    TokenData,
    ZitadelTenantSchema
)
from app.services.portal_activity_log import log_portal_activity
from app.utils import (
    verify_password,
    create_access_token,
    hash_password,
)


def get_portal_user_by_id(db: Session, portal_user_id: str) -> Type[PortalUser]:
    return db.query(PortalUser).filter(PortalUser.id == portal_user_id).first()


def portal_login(db: Session, email: str, password: str) -> PortalTokenResponse:
    """
    Validate portal user credentials, return JWT with role if successful.
    """
    portal_user = db.query(PortalUser).filter(
        PortalUser.email == email,
        PortalUser.active == True
    ).first()
    if not portal_user or not verify_password(password, portal_user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=ErrorMessage.INVALID_CREDENTIALS)

    # Create token
    return PortalTokenResponse(
        token=create_access_token(TokenData(
            id=portal_user.id,
            email=portal_user.email,
            role=portal_user.role,
            tenant_id=portal_user.tenant_id
        )),
        user=PortalUserResponse.model_validate(portal_user),
        role=portal_user.role,  # type: ignore
        tenant_id=portal_user.tenant_id
    )


def create_portal_user(db: Session, payload: PortalUserCreateRequest, portal_user_id: str):
    existing = db.query(PortalUser).filter(PortalUser.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=ErrorMessage.USER_EXISTS)

    new_portal_user = PortalUser(
        email=str(payload.email),
        name=str(payload.name),
        password=hash_password(payload.password),
        role=payload.role,
        tenant_id=payload.tenant_id,
        created_by=portal_user_id
    )
    db.add(new_portal_user)
    db.commit()
    db.refresh(new_portal_user)

    log_portal_activity(db, portal_user_id=portal_user_id, endpoint="/portal-users", action=PortalActivityAction.CREATE)

    return new_portal_user


def list_portal_users(db: Session, filters: ListPortalUsersFilters) -> PaginatedPortalUserResponse:
    query = (
        db.query(
            PortalUser,
            ZitadelTenant.id.label("tenant_id"),
            ZitadelTenant.name.label("tenant_name"),
            ZitadelTenant.zitadel_tenant_id.label("tenant_zitadel_tenant_id"),
        )
        .outerjoin(ZitadelTenant, PortalUser.tenant_id == ZitadelTenant.id)  # Outer join for tenants
    )

    if filters.role:
        query = query.filter(PortalUser.role == filters.role)

    if filters.search_email:
        query = query.filter(PortalUser.email.contains(filters.search_email))

    total = query.count()
    items = (
        query
        .order_by(desc(PortalUser.created_at))
        .offset((filters.page - 1) * filters.size)
        .limit(filters.size)
        .all()
    )

    return PaginatedPortalUserResponse(
        items=[
            PortalUserResponse(
                id=str(u[0].id),
                email=u[0].email,  # type: ignore
                name=str(u[0].name),
                role=u[0].role,  # type: ignore
                active=u[0].active,  # type: ignore
                tenant_id=str(u.tenant_id) if u.tenant_id else None,
                tenant=ZitadelTenantSchema(
                    id=u.tenant_id,
                    name=u.tenant_name,
                    zitadel_tenant_id=u.tenant_zitadel_tenant_id
                ) if u.tenant_id else None
            ) for u in items
        ],
        total=total,
        page=filters.page,
        size=filters.size
    )


def update_portal_user(db: Session, portal_user_id: str, payload: PortalUserUpdateRequest, crr_user_id: str):
    portal_user = get_portal_user_by_id(db, portal_user_id)
    if not portal_user:
        raise HTTPException(status_code=404, detail=ErrorMessage.USER_NOT_FOUND)

    if payload.email is not None:
        # Check if another portal user has that email
        existing = db.query(PortalUser).filter(
            PortalUser.email == payload.email,
            PortalUser.id != portal_user_id
        ).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=ErrorMessage.EMAIL_EXISTS)
        portal_user.email = payload.email

    if payload.password is not None:
        portal_user.password = hash_password(payload.password)

    if payload.tenant_id is not None:
        portal_user.tenant_id = payload.tenant_id

    if payload.name is not None:
        portal_user.name = payload.name

    if payload.active == 1:
        portal_user.active = 1

    portal_user.updated_by = crr_user_id
    db.commit()
    db.refresh(portal_user)

    log_portal_activity(db, portal_user_id=crr_user_id, endpoint="/portal-users", action=PortalActivityAction.UPDATE)

    return portal_user


def delete_portal_user(db: Session, portal_user_id: str, crr_user_id: str) -> GenericMessageResponse:
    portal_user = get_portal_user_by_id(db, portal_user_id)
    if not portal_user:
        raise HTTPException(status_code=404, detail=ErrorMessage.USER_NOT_FOUND)

    portal_user.active = 0
    portal_user.updated_by = crr_user_id
    db.commit()
    db.refresh(portal_user)

    log_portal_activity(db, portal_user_id=crr_user_id, endpoint="/portal-users", action=PortalActivityAction.DELETE)

    return GenericMessageResponse(message=SuccessMessage.PORTAL_USER_REMOVED)

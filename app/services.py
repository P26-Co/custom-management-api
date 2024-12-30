from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Type

from app.constants import (
    DeviceActivityType,
    AdminActivityAction,
    ErrorMessage,
    SuccessMessage
)
from app.models import (
    ZitadelUser,
    AdminUser,
    SharedUser,
    DeviceUser,
    Device,
    DeviceActivityLog,
    AdminActivityLog
)
from app.schemas import (
    TokenResponse,
    GenericMessageResponse,
    PaginatedResponse,
    SharedUserCreateRequest,
    ListZitadelUsersFilters,
    ListDevicesFilters,
    ListDeviceUsersFilters,
    ListSharedUsersFilters,
    ListAdminUsersFilters,
    AdminUserCreateRequest,
    AdminUserResponse,
    AdminUserUpdateRequest,
    DeviceSchema,
    DeviceUserSchema,
    ZitadelUserSchema,
    SharedUserSchema,
    AdminTokenResponse,
    ListDeviceLogsFilters,
    DeviceLogsSchema,
    ListAdminLogsFilters,
    AdminLogsSchema
)
from app.utils import (
    verify_password,
    create_access_token,
    verify_zitadel_credentials,
    hash_password
)


def get_user_by_email(db: Session, email: str) -> Type[ZitadelUser] | None:
    return db.query(ZitadelUser).filter(ZitadelUser.email == email).first()


def get_device_by_device_id(db: Session, device_id: str) -> Type[Device] | None:
    return db.query(Device).filter(Device.device_id == device_id).first()


def get_device_by_id(db: Session, device_id: int) -> Type[Device] | None:
    return db.query(Device).filter(Device.id == device_id).first()


def create_device_if_not_exists(db: Session, device_id: str, user_id: int = None) -> Device:
    device = get_device_by_device_id(db, device_id)
    if not device:
        device = Device(
            device_id=device_id,
            created_by=user_id
        )
        db.add(device)
        db.commit()
        db.refresh(device)
    return device


def get_shared_emails(
        db: Session,
        current_user_id: int,
        current_user_email: str,
        device_id: str,
        device_username: str
) -> List[str]:
    """
    Return a list of emails for owners of the device (device_id + device_username)
    that have shared it with the current user (current_user_id). If the current user
    is themselves the owner of that device, place their email at the beginning.
    """
    owners_emails: List[str] = []

    # Step 1: Look up the actual device by the external_device_id.
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        return owners_emails

    # Step 2: Check if the current user owns that device username on this device
    current_user_device_user = db.query(DeviceUser).filter(
        DeviceUser.zitadel_user_id == current_user_id,
        DeviceUser.device_id == device.id,
        DeviceUser.device_username == device_username
    ).first()

    # If found, place current user's email at the front of the list
    if current_user_device_user:
        owners_emails.append(current_user_email)

    # Step 3: Gather all SharedUser rows that match:
    #   shared_with_user_id == current_user_id, the same device PK, and the same device_username.
    device_user = db.query(DeviceUser).filter(
        DeviceUser.device_username == device_username
    ).first()

    # Step 4: For each shared row, find the corresponding device_user,
    #         then find that device_user's owner => append owner’s email if not the current user.
    if device_user and device_user.zitadel_user_id != current_user_id:
        shared_entry = db.query(SharedUser).filter(
            SharedUser.shared_with_user_id == current_user_id,
            SharedUser.device_user_id == device_user.id
        ).first()

        if shared_entry:
            owner_user = db.query(ZitadelUser).filter(
                ZitadelUser.id == device_user.zitadel_user_id
            ).first()
            if owner_user and str(owner_user.email) not in owners_emails:
                owners_emails.append(str(owner_user.email))

    return owners_emails


def log_activity(
        db: Session,
        user_id: int,
        device_id: int,
        device_username: int,
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


# ---------------------------
# API Services
# ---------------------------

def email_password_login(
        db: Session,
        email: str,
        password: str,
        device_id: str,
        device_username: str
) -> TokenResponse:
    # 1) Validate with Zitadel
    zitadel_user = verify_zitadel_credentials(email, password)
    if not zitadel_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorMessage.INVALID_ZITADEL_CREDENTIALS
        )

    # 2) Upsert user in local DB if it doesn't exist
    user = get_user_by_email(db, email)
    if not user:
        user = ZitadelUser(
            email=email,
            zitadel_user_id=zitadel_user['id'] if 'id' in zitadel_user else f"ext-{email}",  # Some external ID
            tenant_id=zitadel_user['organizationId'] if 'organizationId' in zitadel_user else None,
            name=zitadel_user['displayName'] if 'displayName' in zitadel_user else None,
            created_by=0
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return TokenResponse(
        token=create_access_token({"id": user.id, "email": email}),
        isPinAllowed=bool(user.pin),
        emails=get_shared_emails(db, user.id, user.email, device_id, device_username),
    )


def email_pin_login(
        db: Session,
        email: str,
        pin: str,
        device_id: str,
        device_username: str
) -> TokenResponse:
    user = get_user_by_email(db, email)
    if not user or not user.pin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorMessage.PIN_NOT_SET
        )

    # Verify the pin
    if not verify_password(pin, user.pin):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorMessage.INVALID_PIN
        )

    return TokenResponse(
        token=create_access_token({"id": user.id, "email": email}),
        isPinAllowed=bool(user.pin),
        emails=get_shared_emails(db, user.id, user.email, device_id, device_username),
    )


def set_pin(
        db: Session,
        user_id: int,
        new_pin: str,
        device_id: str,
        device_username: str
) -> TokenResponse:
    user = db.query(ZitadelUser).filter(ZitadelUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=ErrorMessage.USER_NOT_FOUND)

    # Hash the new pin
    user.pin = hash_password(new_pin)
    user.updated_by = user_id
    db.commit()
    db.refresh(user)

    return TokenResponse(
        token=create_access_token({"id": user.id, "email": user.email}),
        isPinAllowed=bool(user.pin),
        emails=get_shared_emails(
            db,
            user.id,  # type: ignore
            str(user.email),
            device_id,
            device_username
        ),
    )


def connect_device(
        db: Session,
        user_id: int,
        device_id: str,
        device_username: str
) -> TokenResponse:
    user = db.query(ZitadelUser).filter(ZitadelUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=ErrorMessage.USER_NOT_FOUND)

    device = create_device_if_not_exists(db, device_id, user_id=user_id)

    # Ensure device_user
    device_user = db.query(DeviceUser).filter(
        DeviceUser.device_id == device.id,
        DeviceUser.zitadel_user_id == user.id,
        DeviceUser.device_username == device_username
    ).first()

    if not device_user:
        device_user = DeviceUser(
            device_id=device.id,
            zitadel_user_id=user.id,  # type: ignore
            device_username=device_username,
            created_by=user.id  # type: ignore
        )
        db.add(device_user)
        db.commit()
        db.refresh(device_user)
        activity_type = DeviceActivityType.device_created
    else:
        activity_type = DeviceActivityType.device_added

    # log activity
    log_activity(
        db,
        user.id,  # type: ignore
        device.id,
        device_user.id,
        login_as=None,
        activity_type=activity_type
    )

    return TokenResponse(
        token=create_access_token({"id": user.id, "email": user.email}),
        isPinAllowed=bool(user.pin),
        emails=get_shared_emails(
            db,
            user.id,  # type: ignore
            str(user.email),
            device_id,
            device_username
        ),
    )


def add_log_activity(
        db: Session,
        user_id: int,
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
    log_activity(
        db,
        user.id,  # type: ignore
        device.id,  # type: ignore
        device_user.id,  # type: ignore
        login_as=login_as,
        activity_type=activity_type
    )

    # return token
    return TokenResponse(token=create_access_token({"id": user.id, "email": user.email}))


def list_device_logs(db: Session, filters: ListDeviceLogsFilters) -> PaginatedResponse:
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
    items = query.offset((filters.page - 1) * filters.size).limit(filters.size).all()

    return PaginatedResponse(
        total=total,
        page=filters.page,
        size=filters.size,
        items=[
            DeviceLogsSchema(
                id=d.id,  # type: ignore
                timestamp=str(d.timestamp),
                activity_type=str(d.activity_type),
                login_as=str(d.login_as) if d.login_as else None,
                device_username=DeviceUserSchema(
                    id=d.device_username,  # type: ignore
                    device_username=d.device_user.device_username,
                    user=ZitadelUserSchema(
                        id=d.device_user.zitadel_user_id,  # type: ignore
                        name=d.device_user.zitadel_user.name,
                        email=d.device_user.zitadel_user.email
                    ),
                ),
                user=ZitadelUserSchema(
                    id=d.zitadel_user_id,  # type: ignore
                    name=d.zitadel_user.name,
                    email=d.zitadel_user.email
                ),
                device=DeviceSchema(
                    id=d.device_id,  # type: ignore
                    name=d.device.name,
                    device_id=d.device.device_id
                )
            )
            for d in items
        ]
    )


def admin_login(db: Session, email: str, password: str) -> AdminTokenResponse:
    """
    Validate admin credentials, return JWT with role=admin if successful.
    """
    admin = db.query(AdminUser).filter(AdminUser.email == email).first()
    if not admin or not verify_password(password, admin.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=ErrorMessage.INVALID_CREDENTIALS)

    # Create admin token
    return AdminTokenResponse(
        token=create_access_token({
            "id": admin.id,
            "email": admin.email,
            "role": "admin"
        }),
        user=AdminUserResponse.model_validate(admin)
    )


def create_admin_user(db: Session, payload: AdminUserCreateRequest, admin_id: int):
    existing = db.query(AdminUser).filter(AdminUser.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=ErrorMessage.USER_EXISTS)

    new_admin = AdminUser(
        email=str(payload.email),
        name=str(payload.name),
        password=hash_password(payload.password)
    )
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)

    log_admin_activity(db, admin_id=admin_id, endpoint="/admin-users", action=AdminActivityAction.CREATE)

    return new_admin


def list_admin_users(db: Session, filters: ListAdminUsersFilters) -> PaginatedResponse:
    query = db.query(AdminUser)

    if filters.search_email:
        query = query.filter(AdminUser.email.contains(filters.search_email))

    total = query.count()
    items = query.offset((filters.page - 1) * filters.size).limit(filters.size).all()

    return PaginatedResponse(
        items=[AdminUserResponse.model_validate(u) for u in items],
        total=total,
        page=filters.page,
        size=filters.size
    )


def get_admin_user_by_id(db: Session, admin_user_id: int) -> Type[AdminUser]:
    admin_user = db.query(AdminUser).filter(AdminUser.id == admin_user_id).first()
    if not admin_user:
        raise HTTPException(status_code=404, detail=ErrorMessage.USER_NOT_FOUND)
    return admin_user


def update_admin_user(db: Session, admin_user_id: int, payload: AdminUserUpdateRequest, admin_id: int):
    admin_user = get_admin_user_by_id(db, admin_user_id)

    if payload.email is not None:
        # Check if another admin user has that email
        existing = db.query(AdminUser).filter(
            AdminUser.email == payload.email,
            AdminUser.id != admin_user_id
        ).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=ErrorMessage.EMAIL_EXISTS)
        admin_user.email = payload.email

    if payload.password is not None:
        admin_user.password = hash_password(payload.password)

    if payload.name is not None:
        admin_user.name = payload.name

    db.commit()
    db.refresh(admin_user)

    log_admin_activity(db, admin_id=admin_id, endpoint="/admin-users", action=AdminActivityAction.UPDATE)

    return admin_user


def delete_admin_user(db: Session, admin_user_id: int, admin_id: int) -> GenericMessageResponse:
    admin_user = get_admin_user_by_id(db, admin_user_id)
    db.delete(admin_user)
    db.commit()

    log_admin_activity(db, admin_id=admin_id, endpoint="/admin-users", action=AdminActivityAction.DELETE)

    return GenericMessageResponse(message=SuccessMessage.USER_REMOVED)


def log_admin_activity(
        db: Session,
        admin_id: int,
        endpoint: str,
        action: str = "",
        zitadel_user_id: int = None,
        device_id: int = None,
        device_user_id: int = None,
        shared_user_id: int = None
) -> None:
    """
    Insert a row in admin_activity_logs to track usage.
    """
    entry = AdminActivityLog(
        admin_user_id=admin_id,
        endpoint=endpoint,
        action=action,
        zitadel_user_id=zitadel_user_id,
        device_id=device_id,
        device_user_id=device_user_id,
        shared_user_id=shared_user_id,
        created_by=admin_id
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)


def list_admin_logs(db: Session, filters: ListAdminLogsFilters) -> PaginatedResponse:
    query = db.query(AdminActivityLog)
    if filters.tenantId:
        query = query.join(ZitadelUser).filter(ZitadelUser.tenant_id == filters.tenantId)

    if filters.adminUserId:
        query = query.filter(AdminActivityLog.admin_user_id == filters.adminUserId)

    if filters.zitadelUserId:
        query = query.filter(AdminActivityLog.zitadel_user_id == filters.zitadelUserId)

    if filters.deviceId:
        query = query.filter(AdminActivityLog.device_id == filters.deviceId)

    if filters.deviceUserId:
        query = query.filter(AdminActivityLog.device_user_id == filters.deviceUserId)

    if filters.sharedUserId:
        query = query.filter(AdminActivityLog.shared_user_id == filters.sharedUserId)

    total = query.count()
    items = query.offset((filters.page - 1) * filters.size).limit(filters.size).all()

    return PaginatedResponse(
        total=total,
        page=filters.page,
        size=filters.size,
        items=[
            AdminLogsSchema(
                id=d.id,  # type: ignore
                timestamp=str(d.timestamp),
                endpoint=str(d.endpoint),
                action=str(d.action) if d.action else None,
                admin_user=AdminUserResponse.model_validate(d.admin_user),
                device_username=DeviceUserSchema(
                    id=d.device_user_id,  # type: ignore
                    device_username=d.device_user.device_username if d.device_user else None,
                    user=ZitadelUserSchema(
                        id=d.device_user.zitadel_user_id,  # type: ignore
                        name=d.device_user.zitadel_user.name,
                        email=d.device_user.zitadel_user.email
                    ) if d.device_user else None,
                ) if d.device_user_id else None,
                user=ZitadelUserSchema(
                    id=d.zitadel_user_id,  # type: ignore
                    name=d.zitadel_user.name if d.zitadel_user else None,
                    email=d.zitadel_user.email if d.zitadel_user else None
                ) if d.zitadel_user_id else None,
                device=DeviceSchema(
                    id=d.device_id,  # type: ignore
                    name=d.device.name if d.device else None,
                    device_id=d.device.device_id if d.device else None
                ) if d.device_id else None,
                shared_user=SharedUserSchema(
                    id=d.shared_user_id,  # type: ignore
                    user=ZitadelUserSchema(
                        id=d.shared_user.shared_with_user_id,  # type: ignore
                        name=d.shared_user.shared_with_user.name,
                        email=d.shared_user.shared_with_user.email
                    ) if d.shared_user else None,
                    device=DeviceSchema(
                        id=d.shared_user.device_user.device_id,  # type: ignore
                        name=d.shared_user.device_user.device.name,
                        device_id=d.shared_user.device_user.device.device_id
                    ) if d.shared_user else None,
                    device_user=DeviceUserSchema(
                        id=d.shared_user.device_user_id,  # type: ignore
                        device_username=d.shared_user.device_user.device_username,
                        user=ZitadelUserSchema(
                            id=d.shared_user.device_user.zitadel_user_id,  # type: ignore
                            name=d.shared_user.device_user.zitadel_user.name,
                            email=d.shared_user.device_user.zitadel_user.email
                        )
                    ) if d.shared_user else None
                ) if d.shared_user_id else None
            )
            for d in items
        ]
    )


def share_device_user(db: Session, admin_id: int, payload: SharedUserCreateRequest) -> SharedUser:
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
        device_user_id=device_user.id,  # type: ignore
        shared_with_user_id=to_share_user.id,  # type: ignore
        created_by=admin_id,
    )
    db.add(new_shared)
    db.commit()
    db.refresh(new_shared)

    log_admin_activity(
        db, admin_id=admin_id, endpoint="/shared-user", action=AdminActivityAction.CREATE, shared_user_id=new_shared.id,
        zitadel_user_id=to_share_user.id, device_user_id=device_user.id  # type: ignore
    )

    return new_shared


def remove_shared_user(db: Session, admin_id: int, shared_user_id: int) -> GenericMessageResponse:
    """
    Deletes a SharedUser entry by its primary key.
    """
    shared_to_remove = db.query(SharedUser).filter(SharedUser.id == shared_user_id).first()
    if not shared_to_remove:
        raise HTTPException(status_code=404, detail=ErrorMessage.SHARED_USER_NOT_FOUND)

    db.delete(shared_to_remove)
    db.commit()

    log_admin_activity(
        db, admin_id=admin_id, endpoint="/shared-user", action=AdminActivityAction.DELETE,
        shared_user_id=shared_user_id,
        zitadel_user_id=shared_to_remove.shared_with_user_id,  # type: ignore
        device_user_id=shared_to_remove.device_user_id  # type: ignore
    )

    return GenericMessageResponse(message=SuccessMessage.SHARED_USER_REMOVED)


def list_zitadel_users(db: Session, filters: ListZitadelUsersFilters) -> PaginatedResponse:
    """
    Return a paginated list of ZitadelUser rows, optionally filtered by tenant_id.
    """
    query = db.query(ZitadelUser)
    if filters.tenantId:
        query = query.filter(ZitadelUser.tenant_id == filters.tenantId)

    total = query.count()
    items = query.offset((filters.page - 1) * filters.size).limit(filters.size).all()

    return PaginatedResponse(
        total=total,
        page=filters.page,
        size=filters.size,
        items=[
            ZitadelUserSchema(
                id=u.id,  # type: ignore
                email=str(u.email),
                name=str(u.name),
                tenant_id=str(u.tenant_id),
                zitadel_user_id=str(u.zitadel_user_id),
            )
            for u in items
        ]
    )


def get_zitadel_user_by_id(db: Session, zitadel_user_id: int) -> Type[ZitadelUser]:
    zitadel_user = db.query(ZitadelUser).filter(ZitadelUser.id == zitadel_user_id).first()
    if not zitadel_user:
        raise HTTPException(status_code=404, detail=ErrorMessage.USER_NOT_FOUND)
    return zitadel_user


def delete_zitadel_user(db: Session, zitadel_user_id: int, admin_id: int) -> GenericMessageResponse:
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
    db.delete(zitadel_user)
    db.commit()

    log_admin_activity(
        db, admin_id=admin_id, endpoint="/zitadel-users", action=AdminActivityAction.DELETE,
        zitadel_user_id=zitadel_user_id
    )

    return GenericMessageResponse(message=SuccessMessage.USER_REMOVED)


def list_devices(db: Session, filters: ListDevicesFilters) -> PaginatedResponse:
    """
    Return a paginated list of Devices, optionally filtered by tenant, user.
    """
    query = db.query(Device)

    if filters.tenantId:
        # To filter by tenant, we join to device_users -> zitadel_user
        query = query.join(DeviceUser).join(ZitadelUser).filter(
            ZitadelUser.tenant_id == filters.tenantId
        )

    if filters.zitadelUserId:
        # Also filter devices for that user: device -> device_users => userId
        query = query.join(DeviceUser).filter(DeviceUser.zitadel_user_id == filters.zitadelUserId)

    query = query.distinct()
    total = query.count()
    items = query.offset((filters.page - 1) * filters.size).limit(filters.size).all()

    return PaginatedResponse(
        total=total,
        page=filters.page,
        size=filters.size,
        items=[
            DeviceSchema(
                id=d.id,  # type: ignore
                device_id=str(d.device_id),
                name=str(d.name) if d.name else None,
                device_users=[
                    DeviceUserSchema(
                        id=du.id,
                        device_username=du.device_username,
                        user=ZitadelUserSchema(
                            id=du.zitadel_user_id,
                            name=du.zitadel_user.name,
                            email=du.zitadel_user.email
                        ),
                    )
                    for du in d.device_users
                ],
            )
            for d in items
        ]
    )


def update_device(db: Session, payload: DeviceSchema, admin_id: int) -> DeviceSchema:
    device = get_device_by_id(db, payload.id)
    if not device:
        raise HTTPException(status_code=404, detail=ErrorMessage.DEVICE_NOT_FOUND)

    if payload.name is not None:
        device.name = payload.name

    db.commit()
    db.refresh(device)

    log_admin_activity(
        db, admin_id=admin_id, endpoint="/devices", action=AdminActivityAction.UPDATE,
        device_id=device.id  # type: ignore
    )

    return DeviceSchema(
        id=device.id,  # type: ignore
        device_id=str(device.device_id),
        name=str(device.name),
    )


def delete_device(db: Session, device_id: int, admin_id: int) -> GenericMessageResponse:
    device_users = db.query(DeviceUser).filter(DeviceUser.device_id == device_id).all()
    for device_user in device_users:
        shared_users = db.query(SharedUser).filter(SharedUser.device_user_id == device_user.id).all()
        for shared_user in shared_users:
            db.delete(shared_user)
        db.delete(device_user)

    device = get_device_by_id(db, device_id)
    db.delete(device)
    db.commit()

    log_admin_activity(
        db, admin_id=admin_id, endpoint="/devices", action=AdminActivityAction.DELETE, device_id=device_id
    )

    return GenericMessageResponse(message=SuccessMessage.USER_REMOVED)


def list_device_users(db: Session, filters: ListDeviceUsersFilters) -> PaginatedResponse:
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
    items = query.offset((filters.page - 1) * filters.size).limit(filters.size).all()

    return PaginatedResponse(
        total=total,
        page=filters.page,
        size=filters.size,
        items=[
            DeviceUserSchema(
                id=d.id,  # type: ignore
                device_username=str(d.device_username),
                user=ZitadelUserSchema(
                    id=d.zitadel_user_id,  # type: ignore
                    name=d.zitadel_user.name,
                    email=d.zitadel_user.email
                ),
                device=DeviceSchema(
                    id=d.device_id,  # type: ignore
                    name=d.device.name,
                    device_id=d.device.device_id
                )
            )
            for d in items
        ]
    )


def get_device_user_by_id(db: Session, device_user_id: int) -> Type[DeviceUser] | None:
    return db.query(DeviceUser).filter(DeviceUser.id == device_user_id).first()


def get_device_user_by_username(db: Session, device_username: str) -> Type[DeviceUser] | None:
    return db.query(DeviceUser).filter(DeviceUser.device_username == device_username).first()


def delete_device_user(db: Session, device_user_id: int, admin_id: int) -> GenericMessageResponse:
    shared_users = db.query(SharedUser).filter(SharedUser.device_user_id == device_user_id).all()
    for shared_user in shared_users:
        db.delete(shared_user)

    device = get_device_user_by_id(db, device_user_id)
    db.delete(device)
    db.commit()

    log_admin_activity(
        db, admin_id=admin_id, endpoint="/device-users", action=AdminActivityAction.DELETE,
        device_user_id=device_user_id, device_id=device.device_id, zitadel_user_id=device.zitadel_user_id
    )

    return GenericMessageResponse(message=SuccessMessage.USER_REMOVED)


def list_shared_users(db: Session, filters: ListSharedUsersFilters) -> PaginatedResponse:
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
    items = query.offset((filters.page - 1) * filters.size).limit(filters.size).all()

    return PaginatedResponse(
        total=total,
        page=filters.page,
        size=filters.size,
        items=[
            SharedUserSchema(
                id=d.id,  # type: ignore
                device_user=DeviceUserSchema(
                    id=d.device_user_id,  # type: ignore
                    device_username=d.device_user.device_username,
                    user=ZitadelUserSchema(
                        id=d.device_user.zitadel_user_id,  # type: ignore
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
                    id=d.shared_with_user_id,  # type: ignore
                    name=d.shared_with_user.name,
                    email=d.shared_with_user.email
                )
            )
            for d in items
        ]
    )

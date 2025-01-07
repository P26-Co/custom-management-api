from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Type

from app.constants import (
    DeviceActivityType,
    ErrorMessage,
)
from app.models import (
    ZitadelUser,
    SharedUser,
    DeviceUser,
    Device,
    ZitadelTenant
)
from app.schemas import (
    TokenResponse,
    ConnectDeviceRequest,
    TokenData
)
from app.services.device import create_device_if_not_exists
from app.services.device_activity_log import create_device_log
from app.utils import (
    verify_password,
    create_access_token,
    verify_zitadel_credentials,
    hash_password,
)


def get_user_by_email(db: Session, email: str) -> Type[ZitadelUser] | None:
    return db.query(ZitadelUser).filter(ZitadelUser.email == email).first()


def get_tenant_by_zitadel_tenant_id(db: Session, zitadel_tenant_id: str) -> Type[ZitadelTenant] | None:
    return db.query(ZitadelTenant).filter(ZitadelTenant.zitadel_tenant_id == zitadel_tenant_id).first()


def get_shared_emails(
        db: Session,
        current_user_id: str,
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
        tenant = get_tenant_by_zitadel_tenant_id(
            db, zitadel_user['organizationId'] if 'organizationId' in zitadel_user else None
        )
        user = ZitadelUser(
            email=email,
            zitadel_user_id=zitadel_user['id'] if 'id' in zitadel_user else f"ext-{email}",  # Some external ID
            tenant_id=str(tenant.id) if tenant else None,
            name=zitadel_user['displayName'] if 'displayName' in zitadel_user else None,
            created_by='SELF'
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return TokenResponse(
        token=create_access_token(TokenData(id=user.id, email=email)),
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
        token=create_access_token(TokenData(id=user.id, email=email)),
        isPinAllowed=bool(user.pin),
        emails=get_shared_emails(db, user.id, user.email, device_id, device_username),
    )


def set_pin(
        db: Session,
        user_id: str,
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
        token=create_access_token(TokenData(id=user.id, email=user.email)),  # type: ignore
        isPinAllowed=bool(user.pin),
        emails=get_shared_emails(
            db,
            str(user.id),
            str(user.email),
            device_id,
            device_username
        ),
    )


def connect_device(db: Session, user_id: str, payload: ConnectDeviceRequest) -> TokenResponse:
    user = db.query(ZitadelUser).filter(ZitadelUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=ErrorMessage.USER_NOT_FOUND)

    device = create_device_if_not_exists(db, payload.deviceId, payload.name, user_id=user_id)

    # Ensure device_user
    device_user = db.query(DeviceUser).filter(
        DeviceUser.device_id == device.id,
        DeviceUser.zitadel_user_id == user.id,
        DeviceUser.device_username == payload.deviceUsername
    ).first()

    if not device_user:
        device_user = DeviceUser(
            device_id=device.id,
            zitadel_user_id=str(user.id),
            device_username=payload.deviceUsername,
            created_by=str(user.id)
        )
        db.add(device_user)
        db.commit()
        db.refresh(device_user)
        activity_type = DeviceActivityType.device_created
    else:
        activity_type = DeviceActivityType.device_added

    # log activity
    create_device_log(
        db,
        str(user.id),
        device.id,
        device_user.id,
        login_as=None,
        activity_type=activity_type
    )

    return TokenResponse(
        token=create_access_token(TokenData(id=user.id, email=user.email)),  # type: ignore
        isPinAllowed=bool(user.pin),
        emails=get_shared_emails(
            db,
            str(user.id),
            str(user.email),
            payload.deviceId,
            payload.deviceUsername
        ),
    )

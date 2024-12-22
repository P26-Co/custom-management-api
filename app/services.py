import base64
import jwt
import requests

from datetime import datetime, timedelta, UTC
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Type

from app.config import settings
from app.constants import ActivityType
from app.models import (
    ZitadelUser,
    Device,
    DeviceUser,
    SharedUser,
    DeviceActivityLog
)
from app.schemas import TokenResponse
from app.utils import hash_pin, verify_pin


def create_access_token(data: dict, expires_delta: int = None):
    if expires_delta is None:
        expires_delta = settings.ACCESS_TOKEN_EXPIRE_MINUTES

    to_encode = data.copy()
    to_encode.update({"exp": datetime.now(UTC) + timedelta(minutes=expires_delta)})

    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )


def decode_access_token(token: str):
    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_user_by_email(db: Session, email: str) -> Type[ZitadelUser] | None:
    return db.query(ZitadelUser).filter(ZitadelUser.email == email).first()


def get_device_by_device_id(db: Session, device_id: str) -> Type[Device] | None:
    return db.query(Device).filter(Device.device_id == device_id).first()


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
    shared_entries = db.query(SharedUser).filter(
        SharedUser.shared_with_user_id == current_user_id,
        SharedUser.device_id == device.id,
        SharedUser.device_username == device_username
    ).all()

    # Step 4: For each shared row, find the corresponding device_user,
    #         then find that device_user's owner => append owner’s email if not the current user.
    for shared in shared_entries:
        device_user = db.query(DeviceUser).filter(
            DeviceUser.device_id == shared.device_id,
            DeviceUser.device_username == shared.device_username
        ).first()
        if device_user and device_user.zitadel_user_id != current_user_id:
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
        device_username: str,
        login_as: str = None,
        activity_type: str = ActivityType.device_login
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
    if not verify_zitadel_credentials(email, password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Zitadel credentials."
        )

    # 2) Upsert user in local DB if it doesn't exist
    user = get_user_by_email(db, email)
    if not user:
        user = ZitadelUser(
            email=email,
            zitadel_user_id=f"ext-{email}",  # Some external ID
            tenant_id="example-tenant",
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
            detail="User or PIN not set."
        )

    # Verify the pin
    if not verify_pin(pin, user.pin):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid PIN."
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
        raise HTTPException(status_code=404, detail="User not found")

    # Hash the new pin
    user.pin = hash_pin(new_pin)
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
        raise HTTPException(status_code=404, detail="User not found")

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
        activity_type = "device_created"
    else:
        activity_type = "device_added"

    # log activity
    log_activity(
        db,
        user.id,  # type: ignore
        device.id,
        device_username,
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
        activity_type: str = "device_login"
) -> TokenResponse:
    user = db.query(ZitadelUser).filter(ZitadelUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    device = get_device_by_device_id(db, device_id)
    if not device:
        raise HTTPException(
            status_code=400,
            detail="Device not found. Must connect the device first."
        )

    # log activity
    log_activity(
        db,
        user.id,  # type: ignore
        device.id,  # type: ignore
        device_username,
        login_as=login_as,
        activity_type=activity_type
    )

    # return token
    return TokenResponse(
        token=create_access_token({"id": user.id, "email": user.email})
    )


def verify_zitadel_credentials(email: str, password: str) -> bool | None:
    try:
        token_res = requests.post(
            f'{settings.ZITADEL_DOMAIN}/oauth/v2/token',
            headers={
                'Authorization': f'Basic {base64.b64encode(
                    f"{settings.ZITADEL_CLIENT_ID}:{settings.ZITADEL_CLIENT_SECRET}".encode()
                ).decode()}',
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            data={
                'grant_type': 'client_credentials',
                'scope': 'openid profile email urn:zitadel:iam:org:project:id:zitadel:aud',
            }
        )
        if token_res.status_code == 200:
            token = token_res.json().get('access_token')
            if not token:
                return None

            session_res = requests.post(
                f'{settings.ZITADEL_DOMAIN}/v2beta/sessions',
                headers={
                    'Accept': 'application/json',
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json',
                },
                json={'checks': {'user': {'loginName': email}}}
            )

            if session_res.status_code == 201:
                session_info = session_res.json()
                session_id = session_info['sessionId']
                if not session_id:
                    return None

                response = requests.patch(
                    f'{settings.ZITADEL_DOMAIN}/v2beta/sessions/{session_id}',
                    headers={
                        'Accept': 'application/json',
                        'Authorization': f'Bearer {token}',
                        'Content-Type': 'application/json',
                    },
                    json={'checks': {'password': {'password': password}}}
                )

                if response.status_code == 200:
                    print('Password verified successfully.')
                    return True

        return None  # zitadel user id

    except Exception as e:
        print(f'Error while verifying password: {e}')
        return None

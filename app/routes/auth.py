from fastapi import Depends, APIRouter
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    LogActivityRequest,
    TokenResponse,
    EmailPasswordRequest,
    EmailPinRequest,
    SetPinRequest,
    ConnectDeviceRequest,
)
from app.services.auth import (
    email_password_login,
    email_pin_login,
    set_pin,
    connect_device,
)
from app.services.device_activity_log import add_device_log
from app.utils import decode_access_token

# Create the Bearer security scheme
bearer_scheme = HTTPBearer()

router = APIRouter()


@router.post("/email-password", response_model=TokenResponse)
def email_password_api(payload: EmailPasswordRequest, db: Session = Depends(get_db)):
    """
    1. API: /email-password
    Req: email, password, deviceId, deviceUsername
    Res: token, isPinAllowed, emails[]
    """
    return email_password_login(
        db,
        str(payload.email),
        payload.password,
        payload.deviceId,
        payload.deviceUsername,
    )


@router.post("/email-pin", response_model=TokenResponse)
def email_pin_api(payload: EmailPinRequest, db: Session = Depends(get_db)):
    """
    2. API: /email-pin
    Req: email, pin, deviceId, deviceUsername
    Res: token, emails[]
    """
    return email_pin_login(
        db,
        str(payload.email),
        payload.pin,
        payload.deviceId,
        payload.deviceUsername
    )


@router.post("/set-pin", response_model=TokenResponse)
def set_pin_api(
        payload: SetPinRequest,
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
        db: Session = Depends(get_db)
):
    """
    3. API: /set-pin
    Req: pin, deviceId, deviceUsername
    Req header: token
    """
    token = decode_access_token(credentials.credentials)
    return set_pin(
        db,
        token.id,
        payload.pin,
        payload.deviceId,
        payload.deviceUsername
    )


@router.post("/connect-device", response_model=TokenResponse)
def connect_device_api(
        payload: ConnectDeviceRequest,
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
        db: Session = Depends(get_db)
):
    """
    4. API: /connect-device
    Req: deviceId, deviceUsername
    Req header: token
    """
    token = decode_access_token(credentials.credentials)
    return connect_device(db, token.id, payload)


@router.post("/log-activity", response_model=TokenResponse)
def log_activity_api(
        payload: LogActivityRequest,
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
        db: Session = Depends(get_db)
):
    """
    5. API: /log-activity
    Req: loginAs, deviceId, deviceUsername, activityType
    Req header: token
    """
    token = decode_access_token(credentials.credentials)
    return add_device_log(
        db,
        token.id,
        payload.loginAs,
        payload.deviceId,
        payload.deviceUsername,
        activity_type=payload.activityType
    )

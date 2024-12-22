from fastapi import FastAPI, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    EmailPasswordRequest,
    EmailPinRequest,
    SetPinRequest,
    ConnectDeviceRequest,
    LogActivityRequest
)
from app.services import (
    decode_access_token,
    email_password_login,
    email_pin_login,
    set_pin,
    connect_device,
    add_log_activity
)

# Create the Bearer security scheme
bearer_scheme = HTTPBearer()

app = FastAPI(
    title="Custom Manager | AppSavi",
    root_path="/api/v1",
    version="1.0.0"
)


@app.post("/email-password")
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


@app.post("/email-pin")
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


@app.post("/set-pin")
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
    decoded = decode_access_token(credentials.credentials)
    return set_pin(
        db,
        decoded.get("id"),
        payload.pin,
        payload.deviceId,
        payload.deviceUsername
    )


@app.post("/connect-device")
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
    decoded = decode_access_token(credentials.credentials)
    return connect_device(
        db,
        decoded.get("id"),
        payload.deviceId,
        payload.deviceUsername
    )


@app.post("/log-activity")
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
    decoded = decode_access_token(credentials.credentials)
    return add_log_activity(
        db,
        decoded.get("id"),
        payload.loginAs,
        payload.deviceId,
        payload.deviceUsername,
        activity_type=payload.activityType
    )

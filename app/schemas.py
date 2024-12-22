from pydantic import BaseModel, EmailStr
from typing import Optional, List


# ----------------------
# Request Schemas
# ----------------------

class EmailPasswordRequest(BaseModel):
    email: EmailStr
    password: str  # This is checked via external Zitadel call
    deviceId: str
    deviceUsername: str


class EmailPinRequest(BaseModel):
    email: EmailStr
    pin: str
    deviceId: str
    deviceUsername: str


class SetPinRequest(BaseModel):
    pin: str
    deviceId: str
    deviceUsername: str


class ConnectDeviceRequest(BaseModel):
    deviceId: str
    deviceUsername: str


class LogActivityRequest(BaseModel):
    loginAs: Optional[str] = None
    deviceId: str
    deviceUsername: str
    activityType: str = "device_login"


# ----------------------
# Response Schemas
# ----------------------

class TokenResponse(BaseModel):
    token: str
    isPinAllowed: Optional[bool] = None
    emails: Optional[List[str]] = None

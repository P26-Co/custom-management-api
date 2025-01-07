from pydantic import BaseModel, EmailStr
from typing import Optional, List


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


class TokenResponse(BaseModel):
    token: str
    isPinAllowed: Optional[bool] = None
    emails: Optional[List[str]] = None


class ConnectDeviceRequest(BaseModel):
    deviceId: str
    deviceUsername: str
    name: Optional[str] = None

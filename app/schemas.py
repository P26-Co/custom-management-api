from pydantic import BaseModel, EmailStr
from typing import Optional, List

from app.constants import DeviceActivityType, Role


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
    activityType: str = DeviceActivityType.device_login


# ----------------------
# Response Schemas
# ----------------------

class TokenResponse(BaseModel):
    token: str
    isPinAllowed: Optional[bool] = None
    emails: Optional[List[str]] = None


# ----------------------
# Admin
# ----------------------
class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str


class AdminUserResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    email: EmailStr
    name: str


class AdminUserCreateRequest(BaseModel):
    email: EmailStr
    name: str
    password: str


class AdminTokenResponse(BaseModel):
    token: str
    role: str = Role.ADMIN
    user: Optional[AdminUserResponse] = None


class AdminUserUpdateRequest(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    password: Optional[str] = None


class ListAdminUsersFilters(BaseModel):
    page: int = 1
    size: int = 10
    search_email: Optional[str] = None


# For /shared-user creation
class SharedUserCreateRequest(BaseModel):
    deviceId: int
    deviceUserId: int
    zitadelUserId: int


class GenericMessageResponse(BaseModel):
    message: str


# ----------------------
# Listing / Pagination
# ----------------------
class ZitadelUserSchema(BaseModel):
    id: int
    email: Optional[str] = None
    name: Optional[str] = None
    tenant_id: Optional[str] = None
    zitadel_user_id: Optional[str] = None


class DeviceUserSchema(BaseModel):
    id: int
    device_username: Optional[str]
    user: Optional[ZitadelUserSchema] = None
    device: Optional["DeviceSchema"] = None


class DeviceSchema(BaseModel):
    id: int
    device_id: Optional[str] = None
    name: Optional[str] = None
    device_users: Optional[List[DeviceUserSchema]] = None


class SharedUserSchema(BaseModel):
    id: int
    device_user: Optional[DeviceUserSchema]
    user: Optional[ZitadelUserSchema]
    device: Optional[DeviceSchema]


class DeviceLogsSchema(BaseModel):
    id: int
    timestamp: str
    activity_type: str
    login_as: Optional[str] = None
    device_username: Optional[DeviceUserSchema] = None
    user: Optional[ZitadelUserSchema] = None
    device: Optional[DeviceSchema] = None


class AdminLogsSchema(BaseModel):
    id: int
    timestamp: str
    endpoint: str
    admin_user: Optional[AdminUserResponse] = None
    action: Optional[str] = None
    device_username: Optional[DeviceUserSchema] = None
    user: Optional[ZitadelUserSchema] = None
    device: Optional[DeviceSchema] = None
    shared_user: Optional[SharedUserSchema] = None


# For listing filters, we can just use query params in the endpoint,
class ListDeviceLogsFilters(BaseModel):
    tenantId: Optional[str] = None
    zitadelUserId: Optional[int] = None
    deviceId: Optional[int] = None
    deviceUserId: Optional[int] = None
    page: int = 1
    size: int = 10


class ListAdminLogsFilters(BaseModel):
    tenantId: Optional[str] = None
    adminUserId: Optional[int] = None
    zitadelUserId: Optional[int] = None
    deviceId: Optional[int] = None
    deviceUserId: Optional[int] = None
    sharedUserId: Optional[int] = None
    page: int = 1
    size: int = 10


class ListZitadelUsersFilters(BaseModel):
    tenantId: Optional[str] = None
    page: int = 1
    size: int = 10


class ListDevicesFilters(BaseModel):
    tenantId: Optional[str] = None
    zitadelUserId: Optional[int] = None
    page: int = 1
    size: int = 10


class ListDeviceUsersFilters(BaseModel):
    tenantId: Optional[str] = None
    zitadelUserId: Optional[int] = None
    deviceId: Optional[int] = None
    page: int = 1
    size: int = 10


class ListSharedUsersFilters(BaseModel):
    tenantId: Optional[str] = None
    zitadelUserId: Optional[int] = None
    deviceUserId: Optional[int] = None
    page: int = 1
    size: int = 10


class PaginatedResponse(BaseModel):
    items: List[
        DeviceSchema |
        ZitadelUserSchema |
        DeviceUserSchema |
        SharedUserSchema |
        AdminUserResponse |
        DeviceLogsSchema |
        AdminLogsSchema
        ]
    total: int
    page: int
    size: int

from __future__ import annotations

from pydantic import BaseModel
from typing import Optional, List

from app.schemas import (
    PaginatedResponse,
    DeviceSchema,
    ZitadelUserSchema,
    FilterRequest
)


class DeviceUserSchema(BaseModel):
    id: str
    device_username: Optional[str]
    user: Optional[ZitadelUserSchema] = None
    device: Optional[DeviceSchema] = None


class ListDeviceUsersFilters(FilterRequest):
    tenantId: Optional[str] = None
    zitadelUserId: Optional[str] = None
    deviceId: Optional[str] = None


class PaginatedDeviceUserResponse(PaginatedResponse):
    items: List[DeviceUserSchema]

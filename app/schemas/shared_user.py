from __future__ import annotations

from pydantic import BaseModel
from typing import Optional, List

from app.schemas import (
    DeviceUserSchema,
    ZitadelUserSchema,
    DeviceSchema,
    PaginatedResponse,
    FilterRequest
)


class SharedUserCreateRequest(BaseModel):
    deviceId: str
    deviceUserId: str
    zitadelUserId: str


class SharedUserSchema(BaseModel):
    id: str
    device_user: Optional[DeviceUserSchema]
    user: Optional[ZitadelUserSchema]
    device: Optional[DeviceSchema]


class ListSharedUsersFilters(FilterRequest):
    tenantId: Optional[str] = None
    zitadelUserId: Optional[str] = None
    deviceUserId: Optional[str] = None


class PaginatedSharedUserResponse(PaginatedResponse):
    items: List[SharedUserSchema]

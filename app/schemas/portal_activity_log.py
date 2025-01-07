from __future__ import annotations

from pydantic import BaseModel
from typing import Optional, List

from app.schemas import (
    PortalUserResponse,
    DeviceUserSchema,
    ZitadelUserSchema,
    DeviceSchema,
    SharedUserSchema,
    PaginatedResponse,
    FilterRequest
)


class PortalLogsSchema(BaseModel):
    id: str
    timestamp: str
    endpoint: str
    action: Optional[str] = None

    portal_user: Optional[PortalUserResponse] = None
    device_user: Optional[DeviceUserSchema] = None
    user: Optional[ZitadelUserSchema] = None
    device: Optional[DeviceSchema] = None
    shared_user: Optional[SharedUserSchema] = None


class ListPortalLogsFilters(FilterRequest):
    tenantId: Optional[str] = None
    portalUserId: Optional[str] = None
    zitadelUserId: Optional[str] = None
    deviceId: Optional[str] = None
    deviceUserId: Optional[str] = None
    sharedUserId: Optional[str] = None


class PaginatedPortalLogsResponse(PaginatedResponse):
    items: List[PortalLogsSchema]

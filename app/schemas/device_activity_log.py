from __future__ import annotations

from pydantic import BaseModel
from typing import Optional, List

from app.constants import DeviceActivityType
from app.schemas import (
    DeviceUserSchema,
    ZitadelUserSchema,
    DeviceSchema,
    PaginatedResponse,
    FilterRequest
)


class LogActivityRequest(BaseModel):
    loginAs: Optional[str] = None
    deviceId: str
    deviceUsername: str
    activityType: str = DeviceActivityType.device_login


class DeviceLogsSchema(BaseModel):
    id: str
    timestamp: str
    activity_type: str
    login_as: Optional[str] = None
    device_user: Optional[DeviceUserSchema] = None
    user: Optional[ZitadelUserSchema] = None
    device: Optional[DeviceSchema] = None


class ListDeviceLogsFilters(FilterRequest):
    tenantId: Optional[str] = None
    zitadelUserId: Optional[str] = None
    deviceId: Optional[str] = None
    deviceUserId: Optional[str] = None


class PaginatedDeviceLogsResponse(PaginatedResponse):
    items: List[DeviceLogsSchema]

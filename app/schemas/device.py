from __future__ import annotations

from pydantic import BaseModel
from typing import Optional, List
from app.schemas import PaginatedResponse, FilterRequest


class DeviceSchema(BaseModel):
    id: str
    device_id: Optional[str] = None
    name: Optional[str] = None
    len_device_users: Optional[int] = 0


class ListDevicesFilters(FilterRequest):
    tenantId: Optional[str] = None
    zitadelUserId: Optional[str] = None


class PaginatedDeviceResponse(PaginatedResponse):
    items: List[DeviceSchema]

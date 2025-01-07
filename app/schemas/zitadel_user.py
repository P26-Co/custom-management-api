from __future__ import annotations

from pydantic import BaseModel
from typing import Optional, List

from app.schemas import (
    PaginatedResponse,
    ZitadelTenantSchema,
    FilterRequest
)


class ZitadelUserSchema(BaseModel):
    id: str
    email: Optional[str] = None
    name: Optional[str] = None
    zitadel_user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    tenant: Optional[ZitadelTenantSchema] = None


class ListZitadelUsersFilters(FilterRequest):
    tenantId: Optional[str] = None


class PaginatedZitadelUserResponse(PaginatedResponse):
    items: List[ZitadelUserSchema]

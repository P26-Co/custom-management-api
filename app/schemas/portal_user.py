from pydantic import BaseModel, EmailStr
from typing import Optional, List

from app.constants import Role
from app.schemas import (
    PaginatedResponse,
    FilterRequest,
    ZitadelTenantSchema
)


class PortalLoginRequest(BaseModel):
    email: EmailStr
    password: str


class PortalUserResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    email: EmailStr
    name: str
    role: Role
    active: bool
    tenant_id: Optional[str] = None
    tenant: Optional[ZitadelTenantSchema] = None


class PortalUserCreateRequest(BaseModel):
    email: EmailStr
    name: str
    password: str
    role: Role
    tenant_id: Optional[str] = None


class PortalTokenResponse(BaseModel):
    token: str
    role: Role
    tenant_id: Optional[str] = None
    user: Optional[PortalUserResponse] = None


class PortalUserUpdateRequest(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    password: Optional[str] = None
    active: Optional[bool] = None
    tenant_id: Optional[str] = None


class ListPortalUsersFilters(FilterRequest):
    role: Optional[Role] = None
    search_email: Optional[str] = None


class PaginatedPortalUserResponse(PaginatedResponse):
    items: List[PortalUserResponse]

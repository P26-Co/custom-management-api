from pydantic import BaseModel
from typing import Optional, List

from app.schemas import PaginatedResponse


class ZitadelTenantSchema(BaseModel):
    id: str
    zitadel_tenant_id: str
    name: Optional[str] = None


class PaginatedZitadelTenantResponse(PaginatedResponse):
    items: List[ZitadelTenantSchema]

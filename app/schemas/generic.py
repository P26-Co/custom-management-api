from pydantic import BaseModel
from typing import List, Any, Optional
from datetime import datetime



class GenericMessageResponse(BaseModel):
    message: str


class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    size: int


class FilterRequest(BaseModel):
    page: int
    size: int


class TokenData(BaseModel):
    id: str
    email: str
    exp: Optional[datetime] = None
    role: Optional[str] = None
    tenant_id: Optional[str] = None

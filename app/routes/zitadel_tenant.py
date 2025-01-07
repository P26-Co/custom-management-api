from fastapi import Depends, APIRouter, Path, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    GenericMessageResponse,
    FilterRequest,
    PaginatedZitadelTenantResponse
)
from app.services.zitadel_tenant import list_zitadel_tenants, delete_zitadel_tenant
from app.utils import decode_access_token

# Create the Bearer security scheme
bearer_scheme = HTTPBearer()

router = APIRouter()


@router.get("/", response_model=PaginatedZitadelTenantResponse)
def get_zitadel_tenants(
        page: int = Query(1),
        size: int = Query(10),
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
        db: Session = Depends(get_db),
):
    decode_access_token(credentials.credentials, only_admin=True)
    return list_zitadel_tenants(
        db,
        FilterRequest(
            page=page,
            size=size
        )
    )


@router.delete("/{tenant_id}", response_model=GenericMessageResponse)
def delete_zitadel_tenant_api(
        tenant_id: str = Path(...),
        db: Session = Depends(get_db),
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    """
    Delete an zitadel tenant by ID.
    """
    token = decode_access_token(credentials.credentials, only_admin=True)
    return delete_zitadel_tenant(db, tenant_id, token.id)

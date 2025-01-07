from fastapi import Depends, Query, Path, APIRouter
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    GenericMessageResponse,
    ListZitadelUsersFilters,
    PaginatedZitadelUserResponse,
)
from app.services.zitadel_user import (
    list_zitadel_users,
    delete_zitadel_user,
)
from app.utils import decode_access_token

# Create the Bearer security scheme
bearer_scheme = HTTPBearer()

router = APIRouter()


@router.get("/", response_model=PaginatedZitadelUserResponse)
def get_zitadel_users(
        tenant_id: str = Query(None),
        page: int = Query(1),
        size: int = Query(10),
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
        db: Session = Depends(get_db),
):
    token = decode_access_token(credentials.credentials, admin_or_manager=True)
    return list_zitadel_users(
        db,
        ListZitadelUsersFilters(
            tenantId=token.tenant_id if token.tenant_id else tenant_id,
            page=page,
            size=size
        )
    )


@router.delete("/{user_id}", response_model=GenericMessageResponse)
def delete_zitadel_user_api(
        user_id: str = Path(...),
        db: Session = Depends(get_db),
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    """
    Delete an zitadel user by ID.
    """
    token = decode_access_token(credentials.credentials, admin_or_manager=True)
    return delete_zitadel_user(db, user_id, token.id)

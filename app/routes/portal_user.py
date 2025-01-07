from fastapi import Depends, Query, Path, APIRouter
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.constants import Role
from app.database import get_db
from app.schemas import (
    GenericMessageResponse,
    PortalTokenResponse,
    PortalLoginRequest,
    PortalUserResponse,
    PortalUserCreateRequest,
    ListPortalUsersFilters,
    PortalUserUpdateRequest,
    PaginatedPortalUserResponse
)
from app.services.portal_user import (
    portal_login,
    create_portal_user,
    list_portal_users,
    get_portal_user_by_id,
    update_portal_user,
    delete_portal_user,
)
from app.utils import decode_access_token

# Create the Bearer security scheme
bearer_scheme = HTTPBearer()

router = APIRouter()


@router.post("/login", response_model=PortalTokenResponse)
def portal_login_api(payload: PortalLoginRequest, db: Session = Depends(get_db)):
    return portal_login(db, str(payload.email), payload.password)


@router.post("/", response_model=PortalUserResponse)
def create_portal_user_api(
        payload: PortalUserCreateRequest,
        db: Session = Depends(get_db),
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    token = decode_access_token(credentials.credentials, only_admin=True)
    return PortalUserResponse.model_validate(create_portal_user(db, payload, token.id))


@router.get("/", response_model=PaginatedPortalUserResponse)
def list_portal_users_api(
        role: Role = Query(None),
        search_email: str = Query(None),
        page: int = Query(1),
        size: int = Query(10),
        db: Session = Depends(get_db),
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    decode_access_token(credentials.credentials, only_admin=True)
    return list_portal_users(
        db,
        ListPortalUsersFilters(
            role=role,
            search_email=search_email,
            page=page,
            size=size,
        )
    )


@router.get("/{user_id}", response_model=PortalUserResponse)
def get_portal_user_api(
        user_id: str = Path(...),
        db: Session = Depends(get_db),
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    decode_access_token(credentials.credentials, only_admin=True)
    return PortalUserResponse.model_validate(get_portal_user_by_id(db, user_id))


@router.patch("/{user_id}", response_model=PortalUserResponse)
def update_portal_user_api(
        payload: PortalUserUpdateRequest,
        user_id: str = Path(...),
        db: Session = Depends(get_db),
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    """
    Update an existing user (email, password).
    """
    token = decode_access_token(credentials.credentials, only_admin=True)
    return PortalUserResponse.model_validate(update_portal_user(db, user_id, payload, token.id))


@router.delete("/{user_id}", response_model=GenericMessageResponse)
def delete_portal_user_api(
        user_id: str = Path(...),
        db: Session = Depends(get_db),
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    """
    Delete an user by ID.
    """
    token = decode_access_token(credentials.credentials, only_admin=True)
    return delete_portal_user(db, user_id, token.id)

from fastapi import FastAPI, Depends, Query, Path
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.utils import decode_access_token
from app.schemas import (
    PaginatedResponse,
    TokenResponse,
    EmailPasswordRequest,
    EmailPinRequest,
    SetPinRequest,
    ConnectDeviceRequest,
    LogActivityRequest,
    AdminTokenResponse,
    AdminLoginRequest,
    SharedUserCreateRequest,
    GenericMessageResponse,
    ListZitadelUsersFilters,
    ListDevicesFilters,
    ListDeviceUsersFilters,
    ListSharedUsersFilters,
    AdminUserResponse,
    AdminUserCreateRequest,
    ListAdminUsersFilters,
    AdminUserUpdateRequest
)
from app.services import (
    email_password_login,
    email_pin_login,
    set_pin,
    connect_device,
    add_log_activity,
    admin_login,
    share_device_user,
    remove_shared_user,
    list_zitadel_users,
    list_devices,
    list_device_users,
    list_shared_users,
    create_admin_user,
    list_admin_users,
    get_admin_user_by_id,
    update_admin_user,
    delete_admin_user
)

# Create the Bearer security scheme
bearer_scheme = HTTPBearer()

app = FastAPI(
    title="Custom Manager | AppSavi",
    root_path="/api/v1",
    version="1.0.0"
)


@app.post("/email-password", response_model=TokenResponse)
def email_password_api(payload: EmailPasswordRequest, db: Session = Depends(get_db)):
    """
    1. API: /email-password
    Req: email, password, deviceId, deviceUsername
    Res: token, isPinAllowed, emails[]
    """
    return email_password_login(
        db,
        str(payload.email),
        payload.password,
        payload.deviceId,
        payload.deviceUsername,
    )


@app.post("/email-pin", response_model=TokenResponse)
def email_pin_api(payload: EmailPinRequest, db: Session = Depends(get_db)):
    """
    2. API: /email-pin
    Req: email, pin, deviceId, deviceUsername
    Res: token, emails[]
    """
    return email_pin_login(
        db,
        str(payload.email),
        payload.pin,
        payload.deviceId,
        payload.deviceUsername
    )


@app.post("/set-pin", response_model=TokenResponse)
def set_pin_api(
        payload: SetPinRequest,
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
        db: Session = Depends(get_db)
):
    """
    3. API: /set-pin
    Req: pin, deviceId, deviceUsername
    Req header: token
    """
    decoded = decode_access_token(credentials.credentials)
    return set_pin(
        db,
        decoded.get("id"),
        payload.pin,
        payload.deviceId,
        payload.deviceUsername
    )


@app.post("/connect-device", response_model=TokenResponse)
def connect_device_api(
        payload: ConnectDeviceRequest,
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
        db: Session = Depends(get_db)
):
    """
    4. API: /connect-device
    Req: deviceId, deviceUsername
    Req header: token
    """
    decoded = decode_access_token(credentials.credentials)
    return connect_device(
        db,
        decoded.get("id"),
        payload.deviceId,
        payload.deviceUsername
    )


@app.post("/log-activity", response_model=TokenResponse)
def log_activity_api(
        payload: LogActivityRequest,
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
        db: Session = Depends(get_db)
):
    """
    5. API: /log-activity
    Req: loginAs, deviceId, deviceUsername, activityType
    Req header: token
    """
    decoded = decode_access_token(credentials.credentials)
    return add_log_activity(
        db,
        decoded.get("id"),
        payload.loginAs,
        payload.deviceId,
        payload.deviceUsername,
        activity_type=payload.activityType
    )


# ----------------------
# Admin Auth
# ----------------------
@app.post("/admin-login", response_model=AdminTokenResponse)
def admin_login_api(payload: AdminLoginRequest, db: Session = Depends(get_db)):
    """
    6. API: /admin-login
    Req: email, password
    Res: token
    """
    return AdminTokenResponse(token=admin_login(db, str(payload.email), payload.password))


@app.post("/shared-user")
def share_device_user_api(
        payload: SharedUserCreateRequest,
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
        db: Session = Depends(get_db)
):
    """
    7. API: POST /shared-user
    Req: deviceId, deviceUserId, zitadelUserId
    Res: The created SharedUser object
    """
    decoded = decode_access_token(credentials.credentials, True)
    return share_device_user(db, decoded.get("id"), payload)


@app.delete("/shared-user/{shared_user_id}", response_model=GenericMessageResponse)
def remove_shared_user_api(
        shared_user_id: int,
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
        db: Session = Depends(get_db)
):
    """
    8. API: DELETE /shared-user
    Req: sharedUserId
    Res: success message
    """
    decoded = decode_access_token(credentials.credentials, True)
    return remove_shared_user(db, decoded.get("id"), shared_user_id)


@app.get("/zitadel-users", response_model=PaginatedResponse)
def get_zitadel_users(
        tenant_id: str = Query(None),
        page: int = Query(1),
        size: int = Query(10),
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
        db: Session = Depends(get_db),
):
    decode_access_token(credentials.credentials, True)
    return list_zitadel_users(
        db,
        ListZitadelUsersFilters(tenantId=tenant_id, page=page, size=size)
    )


@app.get("/devices", response_model=PaginatedResponse)
def get_devices(
        tenant_id: str = Query(None),
        zitadel_user_id: int = Query(None),
        page: int = Query(1),
        size: int = Query(10),
        db: Session = Depends(get_db),
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    decode_access_token(credentials.credentials, True)
    return list_devices(
        db,
        ListDevicesFilters(
            tenantId=tenant_id,
            zitadelUserId=zitadel_user_id,
            page=page,
            size=size
        )
    )


@app.get("/device-users", response_model=PaginatedResponse)
def get_device_users(
        tenant_id: str = Query(None),
        zitadel_user_id: int = Query(None),
        device_id: str = Query(None),
        page: int = Query(1),
        size: int = Query(10),
        db: Session = Depends(get_db),
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    decode_access_token(credentials.credentials, True)
    return list_device_users(
        db,
        ListDeviceUsersFilters(
            tenantId=tenant_id,
            zitadelUserId=zitadel_user_id,
            deviceId=device_id,
            page=page,
            size=size
        )
    )


@app.get("/shared-users", response_model=PaginatedResponse)
def get_shared_users(
        tenant_id: str = Query(None),
        zitadel_user_id: int = Query(None),
        device_user_id: int = Query(None),
        page: int = Query(1),
        size: int = Query(10),
        db: Session = Depends(get_db),
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    decode_access_token(credentials.credentials, True)
    return list_shared_users(
        db,
        ListSharedUsersFilters(
            tenantId=tenant_id,
            zitadelUserId=zitadel_user_id,
            deviceUserId=device_user_id,
            page=page,
            size=size
        )
    )


@app.post("/admin-users", response_model=AdminUserResponse)
def create_admin_user_api(
        payload: AdminUserCreateRequest,
        db: Session = Depends(get_db),
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    decoded = decode_access_token(credentials.credentials, True)
    return AdminUserResponse.model_validate(create_admin_user(db, payload, decoded.get("id")))


@app.get("/admin-users", response_model=PaginatedResponse)
def list_admin_users_api(
        search_email: str = Query(None),
        page: int = Query(1),
        size: int = Query(10),
        db: Session = Depends(get_db),
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    decode_access_token(credentials.credentials, True)
    return list_admin_users(
        db,
        ListAdminUsersFilters(
            search_email=search_email,
            page=page,
            size=size,
        )
    )


@app.get("/admin-users/{user_id}", response_model=AdminUserResponse)
def get_admin_user_api(
        user_id: int = Path(...),
        db: Session = Depends(get_db),
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    decode_access_token(credentials.credentials, True)
    return AdminUserResponse.model_validate(get_admin_user_by_id(db, user_id))


@app.patch("/admin-users/{user_id}", response_model=AdminUserResponse)
def update_admin_user_api(
        payload: AdminUserUpdateRequest,
        user_id: int = Path(...),
        db: Session = Depends(get_db),
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    """
    Update an existing admin user (email, password).
    """
    decoded = decode_access_token(credentials.credentials, True)
    return AdminUserResponse.model_validate(update_admin_user(db, user_id, payload, decoded.get("id")))


@app.delete("/admin-users/{user_id}", response_model=GenericMessageResponse)
def delete_admin_user_api(
        user_id: int = Path(...),
        db: Session = Depends(get_db),
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    """
    Delete an admin user by ID.
    """
    decoded = decode_access_token(credentials.credentials, True)
    return delete_admin_user(db, user_id, decoded.get("id"))

from fastapi import FastAPI
from fastapi.security import HTTPBearer
from fastapi.middleware.cors import CORSMiddleware

from app.routes import (
    auth_routes,
    portal_user_routes,
    portal_activity_log_routes,
    device_routes,
    device_user_routes,
    device_activity_log_routes,
    shared_user_routes,
    task_status_routes,
    zitadel_user_routes,
    zitadel_tenant_routes,
)

# Create the Bearer security scheme
bearer_scheme = HTTPBearer()

app = FastAPI(
    title="Custom Manager | AppSavi",
    root_path="/api/v1",
    version="1.5.0"
)

origins = [
    "http://localhost:4200",
    "http://127.0.0.1:4200",
    "https://manage.appsavi.com"
]

app.add_middleware(
    CORSMiddleware,  # type: ignore
    allow_origins=origins,  # or ["*"] for dev
    allow_credentials=True,
    allow_methods=["*"],  # or specify ['GET','POST',...]
    allow_headers=["*"],  # or specify ['Content-Type','Authorization',...]
)

# Include routers from different modules
app.include_router(auth_routes.router, tags=["On device auth"])
app.include_router(portal_user_routes.router, prefix="/portal-users", tags=["Portal Users"])
app.include_router(portal_activity_log_routes.router, prefix="/portal-logs", tags=["Portal Logs"])
app.include_router(device_routes.router, prefix="/devices", tags=["Devices"])
app.include_router(device_user_routes.router, prefix="/device-users", tags=["Device Users"])
app.include_router(device_activity_log_routes.router, prefix="/device-logs", tags=["Device Logs"])
app.include_router(shared_user_routes.router, prefix="/shared-users", tags=["Shared Users"])
app.include_router(zitadel_user_routes.router, prefix="/zitadel-users", tags=["Zitadel Users"])
app.include_router(zitadel_tenant_routes.router, prefix="/zitadel-tenants", tags=["Zitadel Tenants"])
app.include_router(task_status_routes.router, prefix="/task-status", tags=["Task Status"])

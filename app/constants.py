from enum import Enum


class Role(str, Enum):
    ADMIN = "admin"
    TENANT_MANAGER = "tenant_manager"


class DeviceActivityType(str, Enum):
    device_login = "device_login"
    user_linked = "user_linked"
    device_created = "device_created"
    device_added = "device_added"


class PortalActivityAction(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LIST = "list"


class SuccessMessage(str, Enum):
    SHARED_USER_REMOVED = "Removed shared user successfully"
    TENANT_REMOVED = "Removed tenant successfully"
    USER_REMOVED = "Removed user successfully"
    PORTAL_USER_REMOVED = "Inactive user successfully"


class ErrorMessage(str, Enum):
    UNKNOWN_ERROR = "Unknown error"
    TENANT_NOT_FOUND = "Tenant not found"
    USER_NOT_FOUND = "User not found"
    SHARED_USER_NOT_FOUND = "Shared user not found"
    SHARED_USER_EXISTS = "Shared user already exists for the device user"
    USER_EXISTS = "User already exists"
    EMAIL_EXISTS = "Another user with this email already exists."
    TOKEN_EXPIRED = "Token expired"
    INVALID_TOKEN = "Invalid token"
    INVALID_CREDENTIALS = "Invalid credentials"
    INVALID_ZITADEL_CREDENTIALS = "Invalid Zitadel credentials"
    PIN_NOT_SET = "User or PIN not set"
    INVALID_PIN = "Invalid PIN"
    DEVICE_NOT_FOUND = "Device not found. Must connect the device first."
    DEVICE_USER_NOT_FOUND = "DeviceUser not found"
    INVALID_RIGHTS = "Invalid Rights"
    TASK_STATUS_NOT_FOUND = "No task found for given task_id"


class TaskStatusCode(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"


class TaskType(str, Enum):
    ZitadelUserImport = "zitadel_user_import"


class TaskMessage(str, Enum):
    IMPORTING_USERS = "Importing users from Zitadel"
    IMPORTING_TENANTS = "Importing tenants from Zitadel"

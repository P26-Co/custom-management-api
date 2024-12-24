from enum import Enum


class Role(str, Enum):
    ADMIN = "admin"


class DeviceActivityType(str, Enum):
    device_login = "device_login"
    user_linked = "user_linked"
    device_created = "device_created"
    device_added = "device_added"


class AdminActivityAction(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LIST = "list"


class SuccessMessage(str, Enum):
    SHARED_USER_REMOVED = "Removed shared user successfully"
    USER_REMOVED = "Removed user successfully"


class ErrorMessage(str, Enum):
    UNKNOWN_ERROR = "Unknown error"
    USER_NOT_FOUND = "User not found"
    SHARED_USER_NOT_FOUND = "Shared user not found"
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
    INVALID_ADMIN_RIGHTS = "Invalid Admin Rights"

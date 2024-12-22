from enum import Enum


class ActivityType(str, Enum):
    device_login = "device_login"
    user_linked = "user_linked"
    device_created = "device_created"
    device_added = "device_added"

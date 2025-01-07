from sqlalchemy import (
    Column,
    String,
    ForeignKey,
    DateTime,
    func,
)
from sqlalchemy.orm import relationship
from app.constants import DeviceActivityType
from app.database import Base
from app.models.audit import AuditColumnsMixin


class DeviceActivityLog(Base, AuditColumnsMixin):
    __tablename__ = "device_activity_logs"

    zitadel_user_id = Column(String(36), ForeignKey("zitadel_users.id"))
    device_id = Column(String(36), ForeignKey("devices.id"))
    device_username = Column(String(36), ForeignKey("device_users.id"))
    login_as = Column(String(255), nullable=True)

    # Activity type: e.g. "device_login", "user_linked", "device_created", ...
    activity_type = Column(String(255), nullable=False, default=DeviceActivityType.device_login)
    timestamp = Column(DateTime, default=func.now())

    zitadel_user = relationship("ZitadelUser", backref="device_activity_logs")
    device = relationship("Device", backref="device_activity_logs")
    device_user = relationship("DeviceUser", backref="device_activity_logs")

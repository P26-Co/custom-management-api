from sqlalchemy import (
    Column,
    String,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.audit import AuditColumnsMixin


class DeviceUser(Base, AuditColumnsMixin):
    __tablename__ = "device_users"

    device_id = Column(String(36), ForeignKey("devices.id"), nullable=False)
    zitadel_user_id = Column(String(36), ForeignKey("zitadel_users.id"), nullable=False)
    device_username = Column(String(255), nullable=False)

    device = relationship("Device", back_populates="device_users")
    zitadel_user = relationship("ZitadelUser", back_populates="device_users")

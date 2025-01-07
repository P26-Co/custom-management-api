from sqlalchemy import (
    Column,
    String,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.audit import AuditColumnsMixin


class Device(Base, AuditColumnsMixin):
    __tablename__ = "devices"

    device_id = Column(String(255), unique=True, index=True)
    name = Column(String(255), nullable=True)
    zitadel_user_id = Column(String(36), ForeignKey("zitadel_users.id", ondelete="SET NULL"), nullable=True)

    # Relationship with device_users
    device_users = relationship("DeviceUser", back_populates="device", cascade="all, delete-orphan")
    zitadel_user = relationship("ZitadelUser")

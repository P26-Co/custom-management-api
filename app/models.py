from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    func,
)
from sqlalchemy.orm import relationship

from app.constants import ActivityType
from app.database import Base


class AuditColumnsMixin:
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_by = Column(Integer, nullable=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)


class ZitadelUser(Base, AuditColumnsMixin):
    __tablename__ = "zitadel_users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)

    # Added fields for external synchronization
    zitadel_user_id = Column(String(255), unique=True, index=True, nullable=True)
    tenant_id = Column(String(255), nullable=True)

    # Store encrypted pin in DB
    pin = Column(String(255), nullable=True)

    # Relationship with device_users
    device_users = relationship("DeviceUser", back_populates="zitadel_user", cascade="all, delete-orphan")


class AdminUser(Base, AuditColumnsMixin):
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)

    # store hashed password
    password = Column(String(255), nullable=False)


class Device(Base, AuditColumnsMixin):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(255), unique=True, index=True)

    # Relationship with device_users
    device_users = relationship("DeviceUser", back_populates="device", cascade="all, delete-orphan")


class DeviceUser(Base, AuditColumnsMixin):
    __tablename__ = "device_users"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    zitadel_user_id = Column(Integer, ForeignKey("zitadel_users.id"), nullable=False)
    device_username = Column(String(255), nullable=False)

    device = relationship("Device", back_populates="device_users")
    zitadel_user = relationship("ZitadelUser", back_populates="device_users")


class DeviceActivityLog(Base, AuditColumnsMixin):
    __tablename__ = "device_activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    zitadel_user_id = Column(Integer, ForeignKey("zitadel_users.id"))
    device_id = Column(Integer, ForeignKey("devices.id"))
    device_username = Column(String(255))
    login_as = Column(String(255), nullable=True)

    # Activity type: e.g. "device_login", "user_linked", "device_created", ...
    activity_type = Column(String(255), nullable=False, default=ActivityType.device_login)
    timestamp = Column(DateTime, default=func.now())

    zitadel_user = relationship("ZitadelUser", backref="device_activity_logs")
    device = relationship("Device", backref="device_activity_logs")


class SharedUser(Base, AuditColumnsMixin):
    __tablename__ = "shared_users"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    device_username = Column(String(255), nullable=False)

    # The ID of the user to whom this device_username is shared
    shared_with_user_id = Column(Integer, ForeignKey("zitadel_users.id"), nullable=False)

    shared_with_user = relationship("ZitadelUser")

from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    func,
)
from sqlalchemy.orm import relationship

from app.constants import DeviceActivityType
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
    name = Column(String(255), nullable=True)

    # Store encrypted pin in DB
    pin = Column(String(255), nullable=True)

    # Relationship with device_users
    device_users = relationship("DeviceUser", back_populates="zitadel_user", cascade="all, delete-orphan")


class AdminUser(Base, AuditColumnsMixin):
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)
    name = Column(String(255), nullable=True)

    # store hashed password
    password = Column(String(255), nullable=False)


class Device(Base, AuditColumnsMixin):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(255), unique=True, index=True)
    name = Column(String(255), nullable=True)

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


class SharedUser(Base, AuditColumnsMixin):
    __tablename__ = "shared_users"

    id = Column(Integer, primary_key=True, index=True)
    device_user_id = Column(Integer, ForeignKey("device_users.id"), nullable=False)

    # The ID of the user to whom this device_username is shared
    shared_with_user_id = Column(Integer, ForeignKey("zitadel_users.id"), nullable=False)

    shared_with_user = relationship("ZitadelUser")
    device_user = relationship("DeviceUser")


class DeviceActivityLog(Base, AuditColumnsMixin):
    __tablename__ = "device_activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    zitadel_user_id = Column(Integer, ForeignKey("zitadel_users.id"))
    device_id = Column(Integer, ForeignKey("devices.id"))
    device_username = Column(Integer, ForeignKey("device_users.id"))
    login_as = Column(String(255), nullable=True)

    # Activity type: e.g. "device_login", "user_linked", "device_created", ...
    activity_type = Column(String(255), nullable=False, default=DeviceActivityType.device_login)
    timestamp = Column(DateTime, default=func.now())

    zitadel_user = relationship("ZitadelUser", backref="device_activity_logs")
    device = relationship("Device", backref="device_activity_logs")
    device_user = relationship("DeviceUser", backref="device_activity_logs")


class AdminActivityLog(Base, AuditColumnsMixin):
    __tablename__ = "admin_activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    admin_user_id = Column(Integer, ForeignKey("admin_users.id", ondelete="SET NULL"), nullable=True)
    endpoint = Column(String(255), nullable=False)  # which endpoint was accessed
    action = Column(String(255), nullable=True)  # e.g. "CREATE", "DELETE", "LIST"
    timestamp = Column(DateTime, default=func.now())

    zitadel_user_id = Column(Integer, ForeignKey("zitadel_users.id"), nullable=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=True)
    device_user_id = Column(Integer, ForeignKey("device_users.id"), nullable=True)
    shared_user_id = Column(Integer, ForeignKey("shared_users.id"), nullable=True)

    # optional relationships
    admin_user = relationship("AdminUser", backref="admin_activity_logs")
    zitadel_user = relationship("ZitadelUser", backref="admin_activity_logs")
    device = relationship("Device", backref="admin_activity_logs")
    device_user = relationship("DeviceUser", backref="admin_activity_logs")
    shared_user = relationship("SharedUser", backref="admin_activity_logs")

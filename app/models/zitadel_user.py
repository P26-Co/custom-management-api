from sqlalchemy import (
    Column,
    String,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.audit import AuditColumnsMixin


class ZitadelUser(Base, AuditColumnsMixin):
    __tablename__ = "zitadel_users"

    email = Column(String(255), unique=True, index=True)
    zitadel_user_id = Column(String(255), unique=True, index=True, nullable=True)
    tenant_id = Column(String(36), ForeignKey("zitadel_tenants.id"), nullable=True)
    name = Column(String(255), nullable=True)

    # Store encrypted pin in DB
    pin = Column(String(255), nullable=True)

    # Relationships
    tenant = relationship("ZitadelTenant")
    device_users = relationship("DeviceUser", back_populates="zitadel_user", cascade="all, delete-orphan")

from sqlalchemy import (
    Column,
    String,
    ForeignKey,
    Boolean,
)

from app.constants import Role
from app.database import Base
from app.models.audit import AuditColumnsMixin


class PortalUser(Base, AuditColumnsMixin):
    __tablename__ = "portal_users"

    email = Column(String(255), unique=True, index=True)
    name = Column(String(255), nullable=True)
    role = Column(String(255), nullable=False, default=Role.ADMIN)
    tenant_id = Column(String(36), ForeignKey("zitadel_tenants.id"), nullable=True, default=None)
    active = Column(Boolean, nullable=False, default=True)

    # store hashed password
    password = Column(String(255), nullable=False)

from sqlalchemy import (
    Column,
    String,
)
from app.database import Base
from app.models.audit import AuditColumnsMixin


class ZitadelTenant(Base, AuditColumnsMixin):
    __tablename__ = "zitadel_tenants"

    zitadel_tenant_id = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=True)

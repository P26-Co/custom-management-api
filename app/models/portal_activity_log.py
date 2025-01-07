from sqlalchemy import (
    Column,
    String,
    ForeignKey,
    DateTime,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.audit import AuditColumnsMixin


class PortalActivityLog(Base, AuditColumnsMixin):
    __tablename__ = "portal_activity_logs"

    portal_user_id = Column(String(36), ForeignKey("portal_users.id", ondelete="SET NULL"), nullable=True)
    endpoint = Column(String(255), nullable=False)  # which endpoint was accessed
    action = Column(String(255), nullable=True)  # e.g. "CREATE", "DELETE", "LIST"
    timestamp = Column(DateTime, default=func.now())

    zitadel_user_id = Column(String(36), ForeignKey("zitadel_users.id", ondelete="SET NULL"), nullable=True)
    zitadel_tenant_id = Column(String(36), ForeignKey("zitadel_tenants.id", ondelete="SET NULL"), nullable=True)
    device_id = Column(String(36), ForeignKey("devices.id", ondelete="SET NULL"), nullable=True)
    device_user_id = Column(String(36), ForeignKey("device_users.id", ondelete="SET NULL"), nullable=True)
    shared_user_id = Column(String(36), ForeignKey("shared_users.id", ondelete="SET NULL"), nullable=True)

    # optional relationships
    portal_user = relationship("PortalUser", backref="portal_activity_logs")
    zitadel_user = relationship("ZitadelUser", backref="portal_activity_logs")
    zitadel_tenant = relationship("ZitadelTenant", backref="portal_activity_logs")
    device = relationship("Device", backref="portal_activity_logs")
    device_user = relationship("DeviceUser", backref="portal_activity_logs")
    shared_user = relationship("SharedUser", backref="portal_activity_logs")

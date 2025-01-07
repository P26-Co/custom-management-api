from sqlalchemy import (
    Column,
    ForeignKey,
    String,
)
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.audit import AuditColumnsMixin


class SharedUser(Base, AuditColumnsMixin):
    __tablename__ = "shared_users"

    device_user_id = Column(String(36), ForeignKey("device_users.id"), nullable=False)
    shared_with_user_id = Column(String(36), ForeignKey("zitadel_users.id"), nullable=False)

    shared_with_user = relationship("ZitadelUser")
    device_user = relationship("DeviceUser")

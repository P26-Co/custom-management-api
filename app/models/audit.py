import uuid

from sqlalchemy import (
    Column,
    DateTime,
    func,
    String,
)


class AuditColumnsMixin:
    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))

    created_by = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_by = Column(String(36), nullable=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

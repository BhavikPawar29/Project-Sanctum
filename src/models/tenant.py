from sqlalchemy import Boolean, Column, Integer, String, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from src.db.session import Base

class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    team_size = Column(Integer, nullable=True)
    location = Column(String, nullable=True)
    sector = Column(String, unique=False)
    contact = Column(String, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    is_deleted = Column(Boolean, default=False)

    tenant_memberships = relationship("TenantMembership", back_populates="tenant")

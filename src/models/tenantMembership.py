import uuid
import datetime
from sqlalchemy import Column, DateTime, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.db.session import Base


class TenantMembership(Base):
    __tablename__ = "tenant_memberships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    role = Column(String, nullable=False)

    joined_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("Users", back_populates="tenant_memberships")
    tenant = relationship("Tenant", back_populates="tenant_memberships")


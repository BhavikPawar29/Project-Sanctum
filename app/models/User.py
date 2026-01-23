
from datetime import datetime
import uuid
from sqlalchemy import Boolean, DateTime, String, Column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.database_connection import Base

class Users(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(), unique=True, nullable=False)
    password = Column(String(), nullable=False)
    name = Column(String(), nullable=False)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    tenant_memberships = relationship("TenantMembership", back_populates="user")

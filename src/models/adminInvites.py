import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from src.db.session import Base

class AdminInvite(Base):
    __tablename__ = "admin_invites"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    role = Column(String(50), default="member")
    status = Column(String(20), default="PENDING")

    invited_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    invited_at = Column(DateTime, default=datetime.utcnow)
    decision_at = Column(DateTime, nullable=True)

    note = Column(Text, nullable=True)

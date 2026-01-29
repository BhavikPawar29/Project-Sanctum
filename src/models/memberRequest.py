import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from src.db.session import Base

class MemberRequest(Base):
    __tablename__ = "member_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    status = Column(String(20), default="PENDING")  # PENDING / APPROVED / REJECTED

    requested_at = Column(DateTime, default=datetime.utcnow)
    decision_at = Column(DateTime, nullable=True)

    note = Column(Text, nullable=True)
    decided_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

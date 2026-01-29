from uuid import UUID
from pydantic import BaseModel
from datetime import datetime
#from typing import Optional
from typing import Optional


class MembershipInviteRequest(BaseModel):
    email: str
    role_id: str

class MembershipAddRequest(BaseModel):
    tenant_id: UUID

class MembershipPublic(BaseModel):
    id: UUID
    user_id: str
    tenant_id: str
    role_id: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class MembershipSummary(BaseModel):
    tenant_id: UUID
    tenant_name: str
    role_name: str


class MembershipRequestResponse(BaseModel):
    request_id: UUID
    tenant_id: UUID
    status: str
    requested_at: datetime
    decision_at: Optional[datetime]
    note: Optional[str]


class ApproveRequestSchema(BaseModel):
    note: Optional[str] = None


class RejectRequestSchema(BaseModel):
    note: str

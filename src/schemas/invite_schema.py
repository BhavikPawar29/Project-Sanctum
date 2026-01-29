from pydantic import BaseModel, EmailStr
from uuid import UUID
from typing import Optional
from datetime import datetime

class InviteUserRequest(BaseModel):
    email: EmailStr
    role: str = "member"


class InviteResponse(BaseModel):
    invite_id: UUID
    tenant_id: UUID
    user_id: UUID
    role: str
    status: str


class InviteDecisionSchema(BaseModel):
    accept: bool
    note: Optional[str] = None

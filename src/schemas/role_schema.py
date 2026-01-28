from uuid import UUID
from pydantic import BaseModel
from typing import List, Optional


class RoleCreate(BaseModel):
    name: str
    permissions: List[str]

class RoleUpdate(BaseModel):
    r_name: str | None = None
    permissions: list[str] | None = None

class AssignRoleRequest(BaseModel):
    user_id: UUID
    role_id: UUID

class RolePublic(BaseModel):
    id: UUID
    name: str
    tenant_id: Optional[UUID]

    class Config:
        from_attributes = True

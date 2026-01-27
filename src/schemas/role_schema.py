from uuid import UUID
from pydantic import BaseModel
from typing import List, Optional


class RoleCreate(BaseModel):
    name: str
    permissions: List[str]


class RolePublic(BaseModel):
    id: UUID
    name: str
    tenant_id: Optional[UUID]

    class Config:
        from_attributes = True

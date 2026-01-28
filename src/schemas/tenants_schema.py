from uuid import UUID
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class TenantCreate(BaseModel):

    name: str = Field(..., min_length=2, max_length=255)
    team_size: Optional[int] = None
    location: Optional[str] = None
    sector: Optional[str] = None
    contact: Optional[str] = None

class TenantUpdate(BaseModel):
    name: Optional[str] = None
    team_size: Optional[int] = None
    location: Optional[str] = None
    sector: Optional[str] = None
    contact: Optional[str] = None


class TenantPublic(BaseModel):
    id: UUID
    name: str
    owner_id: UUID
    
    team_size: Optional[int] = None
    location: Optional[str] = None
    sector: Optional[str] = None
    contact: Optional[str] = None

    created_at: datetime
    role: str

    class Config:
        from_attributes = True


class TenantSummary(BaseModel):
    id: UUID
    name: str
    role: str


class TenantSwitchRequest(BaseModel):
    tenant_id: UUID

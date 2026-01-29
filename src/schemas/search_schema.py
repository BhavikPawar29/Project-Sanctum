from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID

class AdvancedSearchRequest(BaseModel):
    query: Optional[str] = None
    entity_types: Optional[List[str]] = None  # users, projects, tenants
    #tenant_id: Optional[UUID] = None
    limit: Optional[int] = 20
    offset: Optional[int] = 0
    sort_by: Optional[str] = "created_at"
    order: Optional[str] = "desc"

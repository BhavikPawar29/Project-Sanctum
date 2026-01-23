from pydantic import BaseModel, Field
from typing import Optional

class Tenant(BaseModel):

    name: str
    team_size: Optional[int] = None
    location: Optional[str] = None
    sector: Optional[str] = None
    contact: Optional[str] = None
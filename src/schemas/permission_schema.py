from uuid import UUID
from pydantic import BaseModel


class PermissionPublic(BaseModel):
    id: UUID
    name: str

    class Config:
        from_attributes = True

from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime


class InviteUserRequest(BaseModel):
    email: EmailStr
    role: str = "member"


# class InviteUserResponse(BaseModel):
#     status: str
#     user_id: UUID
#     tenant_id: UUID
#     role: str

class TenantUser(BaseModel):
    user_id: UUID
    email: str
    name: str
    role: str
    joined_at: datetime


class ListTenantUsersResponse(BaseModel):
    tenant_id: UUID
    count: int
    users: list[TenantUser]

class UpdateUserRoleRequest(BaseModel):
    tenant_id: UUID
    new_role: str


class UpdateUserRoleResponse(BaseModel):
    status: str
    user_id: UUID
    tenant_id: UUID
    new_role: str

    
class RemoveUserResponse(BaseModel):
    status: str
    user_id: UUID
    tenant_id: UUID

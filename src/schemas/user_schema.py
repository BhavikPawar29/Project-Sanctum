from datetime import datetime
import re
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, SecretStr, field_validator
from typing import Optional, List

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: SecretStr = Field(..., min_length=8)

    
    @field_validator("password")
    def password_complexity(cls, value:SecretStr):

        """
        Docstring for password_complexity
        
        :param cls: Self-refernce of the class
        :param value: password passed through the @field_validator
        """
        pwd = value.get_secret_value()
        if not (
            re.search(r"[A-Z]", pwd) 
            and re.search(r"[a-z]", pwd) 
            and re.search(r"[0-9]", pwd), 
        ):
            raise ValueError(
                "Error: Password must contain at least one upper case letter, one lower case letter and an digite"
                )
        
        return value
    

class UserPublic(UserBase):
    id: UUID
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserMe(UserPublic):
    tenants: Optional[List["TenantSummary"]] = []


from schemas.tenants_schema import TenantSummary
UserMe.model_rebuild()

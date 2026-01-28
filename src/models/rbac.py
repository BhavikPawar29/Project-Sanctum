from uuid import uuid4
from sqlalchemy.dialects.postgresql import UUID
from src.db.session import Base
from sqlalchemy import Column ,ForeignKey, String


class Role(Base):
    __tablename__ = "roles"

    id = Column(UUID, primary_key=True, default=uuid4)
    r_name = Column(String, nullable=False)
    tenant_id = Column(UUID, index=True)


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(UUID, primary_key=True, default=uuid4)
    code = Column(String, unique=True, nullable=False)


class RolePermission(Base):
    __tablename__ = "role_permissions"

    role_id = Column(UUID, ForeignKey("roles.id"), primary_key=True)
    permission_id = Column(UUID, ForeignKey("permissions.id"), primary_key=True)


class UserRole(Base):
    __tablename__ = "user_roles"

    user_id = Column(UUID, primary_key=True)
    role_id = Column(UUID, ForeignKey("roles.id"), primary_key=True)
    tenant_id = Column(UUID, index=True)

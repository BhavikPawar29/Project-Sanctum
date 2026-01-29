from sqlalchemy.orm import Session

from src.models.user import Users as UserModel
from src.models.projects import Project as ProjectModel
from src.models.tenant import Tenant as TenantModel
from src.models.tenantMembership import TenantMembership as TenantMembershipModel


def basic_search(db: Session, tenant_id: str, user_id: str, query: str):
    results = []

    users = db.query(UserModel).join(
        TenantMembershipModel,
        TenantMembershipModel.user_id == UserModel.id
    ).filter(
        TenantMembershipModel.tenant_id == tenant_id,
        UserModel.email.ilike(f"%{query}%")
    ).limit(10).all()

    for u in users:
        results.append({
            "type": "user",
            "id": str(u.id),
            "label": u.email
        })

    projects = db.query(ProjectModel).filter(
        ProjectModel.tenant_id == tenant_id,
        ProjectModel.name.ilike(f"%{query}%")
    ).limit(10).all()

    for p in projects:
        results.append({
            "type": "project",
            "id": str(p.id),
            "label": p.name
        })

    tenants = db.query(TenantModel).join(
        TenantMembershipModel,
        TenantMembershipModel.tenant_id == TenantModel.id
    ).filter(
        TenantMembershipModel.user_id == user_id,
        TenantModel.name.ilike(f"%{query}%")
    ).limit(5).all()

    for t in tenants:
        results.append({
            "type": "tenant",
            "id": str(t.id),
            "label": t.name
        })

    return results

def advanced_search(db: Session, tenant_id: str, user_id: str, payload):
    results = []
    query = payload.query or ""

    entity_types = payload.entity_types or ["users", "projects", "tenants", "email"]

    if "users" in entity_types:
        users = db.query(UserModel).join(
            TenantMembershipModel,
            TenantMembershipModel.user_id == UserModel.id
        ).filter(
            TenantMembershipModel.tenant_id == tenant_id,
            UserModel.name.ilike(f"%{query}%")
        ).limit(payload.limit).offset(payload.offset).all()

        for u in users:
            results.append({
                "type": "user",
                "id": str(u.id),
                "name": u.name,
                "email": u.email
            })

    if "email" in entity_types:
        users = db.query(UserModel).join(
            TenantMembershipModel,
            TenantMembershipModel.user_id == UserModel.id
        ).filter(
            TenantMembershipModel.tenant_id == tenant_id,
            UserModel.email.ilike(f"%{query}%")
        ).limit(payload.limit).offset(payload.offset).all()

        for u in users:
            results.append({
                "type": "user",
                "id": str(u.id),
                "name": u.name,
                "email": u.email
            })

    if "projects" in entity_types:
        projects = db.query(ProjectModel).filter(
            ProjectModel.tenant_id == tenant_id,
            ProjectModel.name.ilike(f"%{query}%")
        ).limit(payload.limit).offset(payload.offset).all()

        for p in projects:
            results.append({
                "type": "project",
                "id": str(p.id),
                "name": p.name,
                "status": p.status
            })

    if "tenants" in entity_types:
        tenants = db.query(TenantModel).join(
            TenantMembershipModel,
            TenantMembershipModel.tenant_id == TenantModel.id
        ).filter(
            TenantMembershipModel.user_id == user_id,
            TenantModel.name.ilike(f"%{query}%")
        ).limit(payload.limit).offset(payload.offset).all()

        for t in tenants:
            results.append({
                "type": "tenant",
                "id": str(t.id),
                "name": t.name
            })

    return results

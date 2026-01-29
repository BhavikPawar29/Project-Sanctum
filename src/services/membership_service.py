from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from src.models.memberRequest import MemberRequest
from src.models.tenantMembership import TenantMembership as TenantMembershipModel


def require_tenant_admin(db, user_id, tenant_id):
    membership = db.query(TenantMembershipModel).filter(
        TenantMembershipModel.user_id == user_id,
        TenantMembershipModel.tenant_id == tenant_id
    ).first()

    if not membership or membership.role not in ["owner", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to perform this action!!!"
            )

    return membership

def create_member_request(db: Session, user_id, tenant_id):
    req = MemberRequest(
        user_id=user_id,
        tenant_id=tenant_id,
        status="PENDING"
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


def approve_request(db: Session, req, admin_id, note=None):
    req.status = "APPROVED"
    req.note = note
    req.decision_at = datetime.utcnow()
    req.decided_by = admin_id

    membership = TenantMembershipModel(
        user_id=req.user_id,
        tenant_id=req.tenant_id,
        role="member"
    )

    db.add(membership)
    db.commit()

    return req


def reject_request(db: Session, req, admin_id, note):
    req.status = "REJECTED"
    req.note = note
    req.decision_at = datetime.utcnow()
    req.decided_by = admin_id

    db.commit()
    return req

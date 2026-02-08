from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Request, status
from typing import List
from src.db.transactions import transactional
from src.schemas.membership_schema import MembershipAddRequest, MembershipRequestResponse
from src.services.membership_service import create_member_request
from src.core.security import create_access_token, oauth2_scheme
from src.db.session import get_db
from src.schemas.tenants_schema import TenantSummary, TenantSwitchRequest
from src.models.tenantMembership import TenantMembership as TenantMembershipModel
from src.models.tenant import Tenant as TenantModel
from src.models.memberRequest import MemberRequest as MemberRequestModel

router = APIRouter(
    prefix="/users", 
    tags=["My Workspace"],
    dependencies=[Depends(oauth2_scheme)]
    )


@router.post("/request", status_code=status.HTTP_200_OK)
async def request_membership(request: Request, request_in: MembershipAddRequest, db: Session = Depends(get_db)):
    user_id = request.state.user_id

    tenant_exists = db.query(TenantModel).filter(
        TenantModel.id == request_in.tenant_id
    ).first()

    if not tenant_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found!!!"
        )

    membership = db.query(
        TenantMembershipModel
    ).filter(
        TenantMembershipModel.user_id == user_id,
        TenantMembershipModel.tenant_id == request_in.tenant_id
    ).first()

    if membership:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with same ID already a member!!!"
        )
    
    with transactional(db):
        member_request = create_member_request(
            db,
            user_id,
            request_in.tenant_id
        )
    
    return member_request


@router.get("/my-workspaces", response_model=List[TenantSummary], status_code=status.HTTP_200_OK)
def get_my_tenants(request: Request, db: Session = Depends(get_db)):

    user_id = request.state.user_id

    memberships = db.query(
        TenantMembershipModel
    ).filter(
        TenantMembershipModel.user_id == user_id
    ).all()

    if not memberships:
        return []

    return [
        {
            "id": m.tenant_id,
            "name": m.tenant.name,
            "role": m.role
        }

        for m in memberships
    ]

@router.get("/my-requests", response_model=List[MembershipRequestResponse])
def list_my_requests(request: Request, db: Session = Depends(get_db)):
    user_id = request.state.user_id

    requests = db.query(MemberRequestModel).filter(
        MemberRequestModel.user_id == user_id
    ).order_by(MemberRequestModel.requested_at.desc()).all()

    return [
        {
            "request_id": r.id,
            "tenant_id": r.tenant_id,
            "status": r.status,
            "requested_at": r.requested_at,
            "decision_at": r.decision_at,
            "note": r.note
        }
        for r in requests
    ]



@router.post("/switch", status_code=status.HTTP_200_OK)
async def switch_tenant(data: TenantSwitchRequest, request: Request, db: Session = Depends(get_db)):

    user_id = request.state.user_id

    membership = db.query(TenantMembershipModel).filter(
        TenantMembershipModel.user_id == user_id,
        TenantMembershipModel.tenant_id == data.tenant_id
    ).first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not member of this tenant!!!"
        )
    
    new_token = create_access_token(
        user_id=user_id,
        tenant_id=str(membership.tenant_id),
        role=membership.role
    )

    return {
        "access_token": new_token,
        "tenant_id": str(membership.tenant_id),
        "role": membership.role
    }

from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Request, status
from src.schemas.invite_schema import InviteDecisionSchema
from src.models.adminInvites import AdminInvite as AdminInviteModel
from src.db.session import get_db
from datetime import datetime
from src.core.security import oauth2_scheme
from src.models.user import Users as UserModel
from src.models.tenantMembership import TenantMembership as TenantMembershipModel
from src.services.redis_tokens import revoke_refresh_token

router = APIRouter(
    prefix="/users", 
    tags=["Users"],
    dependencies=[Depends(oauth2_scheme)]
    )


@router.get("/me", status_code=status.HTTP_200_OK)
def get_me(request: Request, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):

    user_id = request.state.user_id

    user = db.query(
        UserModel
    ).filter(
        UserModel.id == user_id
    ).first()

    membership = db.query(
        TenantMembershipModel
    ).filter(
        TenantMembershipModel.user_id == user_id
    ).all()

    tenants = [
            {
                "id": m.tenant_id,
                "name": m.tenant.name,
                "role": m.role
            } 
            for m in membership
        ]
    
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "is_verified": getattr(user, "is_verified", True),
        "created_at": user.created_at,
        "tenants": tenants
    }

@router.get("/invites", status_code=status.HTTP_200_OK)
def list_my_invites(request: Request, db: Session = Depends(get_db)):

    invites = db.query(AdminInviteModel).filter(
        AdminInviteModel.user_id == request.state.user_id
    ).order_by(
        AdminInviteModel.invited_at.desc()
        ).all()

    return [
        {
            "invite_id": i.id,
            "tenant_id": i.tenant_id,
            "role": i.role,
            "status": i.status,
            "invited_at": i.invited_at,
            "note": i.note
        }
        for i in invites
    ]

@router.post("/invites/{invite_id}/respond", status_code=status.HTTP_201_CREATED)
def respond_to_invite(invite_id: UUID, payload: InviteDecisionSchema, request: Request, db: Session = Depends(get_db)):
    
    invite = db.query(
            AdminInviteModel
        ).filter(
            AdminInviteModel.id==invite_id
        ).first()

    if not invite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Invite not found!!!"
        )

    if invite.user_id != UUID(request.state.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Not your invite!!!"
        )
        

    if invite.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail="Invite already processed!!!"
        )

    invite.status = "ACCEPTED" if payload.accept else "REJECTED"
    invite.note = payload.note
    invite.decision_at = datetime.utcnow()

    if payload.accept:
        membership = TenantMembershipModel(
            user_id=invite.user_id,
            tenant_id=invite.tenant_id,
            role=invite.role
        )
        db.add(membership)

    db.commit()

    return {
        "status": invite.status,
        "tenant_id": invite.tenant_id,
        "role": invite.role
    }

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, token: str = Depends(oauth2_scheme)):
    user_id = request.state.user_id
    revoke_refresh_token(str(user_id))
    return {"message": "Logged out successfully"}


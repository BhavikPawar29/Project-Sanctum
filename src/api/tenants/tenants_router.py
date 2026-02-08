from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, status, Request
from src.services.audit_service import log_audit_event
from src.schemas.invite_schema import InviteResponse
from src.models.adminInvites import AdminInvite as AdminInviteModel
from src.services.membership_service import require_tenant_admin
from src.db.session import get_db
from src.core.security import oauth2_scheme
from src.models.user import Users as UserModel
from src.models.tenant import Tenant as TenantModel
from src.models.tenantMembership import TenantMembership as TenantMembershipModel
from src.schemas.tenants_schema import TenantCreate as TenantCreateSchema, TenantOut, TenantPublic, TenantUpdate
from src.schemas.team_schema import InviteUserRequest, ListTenantUsersResponse, RemoveUserResponse, UpdateUserRoleRequest, UpdateUserRoleResponse

router = APIRouter(
    prefix="/tenants", 
    tags=["Tenants"],
    dependencies=[Depends(oauth2_scheme)]
)

@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_tenant(payload: TenantCreateSchema, request: Request, db: Session = Depends(get_db)):

    user_id = request.state.user_id

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNtenantIZED, 
            detail="Untenantized!!!"
            )
    
    existing = db.query(
            TenantModel
        ).filter(
            TenantModel.name == payload.name
        ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tenant name already exists!!!"
        )
    
    tenant = TenantModel(
        name=payload.name,
        team_size=payload.team_size,
        location=payload.location,
        sector=payload.sector,
        contact=payload.contact
    )

    db.add(tenant)
    db.commit()
    db.refresh(tenant)

    user_obj = db.query(
        UserModel
    ).filter(
        UserModel.id == user_id
    ).first()

    membership = TenantMembershipModel(
        user=user_obj,
        tenant=tenant,
        role="owner"
    )

    db.add(membership)
    db.commit()

    log_audit_event(db , action="membertenant.create", resource=f"tenant:{str(tenant.id)}", request=request)

    return {
        "message": "Tenant created successfully",
        "tenant": {
            "id": str(tenant.id),
            "name": tenant.name,
            "team_size": tenant.team_size,
            "location": tenant.location,
            "sector": tenant.sector,
            "contact": tenant.contact,
            "created_at": tenant.created_at,
        },
        "role_assigned": "owner"
    }


@router.get("/tenant_id", response_model=TenantPublic, status_code=status.HTTP_200_OK)
def get_tenant(tenant_id: UUID, request: Request, db: Session = Depends(get_db)):

    user_id = request.state.user_id

    membership = db.query(TenantMembershipModel).filter(
        TenantMembershipModel.user_id == user_id,
        TenantMembershipModel.tenant_id == tenant_id
    ).first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not member of this tenant!!!"
        )

    tenant = db.query(
            TenantModel
        ).filter(
            TenantModel.id == tenant_id
        ).first()

    # return {
    #     "id": tenant.id,
    #     "name": tenant.name,
    #     "owner_id": membership.user_id,
    #     "created_at": tenant.created_at,
    #     "role": membership.role
    # }
    return {
        "id": tenant.id,
        "name": tenant.name,
        "owner_id": membership.user_id,
        "team_size": tenant.team_size,
        "location": tenant.location,
        "sector": tenant.sector,
        "contact": tenant.contact,
        "created_at": tenant.created_at,
        "role": membership.role,
    }


@router.patch("/{tenant_id}", response_model=TenantOut, status_code=status.HTTP_200_OK)
async def update_tenant(request: Request, tenant_id: UUID, update: TenantUpdate, db: Session = Depends(get_db)):
    
    require_tenant_admin(db, request.state.user_id, tenant_id)

    tenant = db.query(
        TenantModel
    ).filter(
        TenantModel.id == tenant_id
    ).first()

    if not tenant: 
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant details not found!!!"
        )

    update_data = update.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update!"
        )

    for field, value in update_data.items():
        setattr(tenant, field, value) # --> tenant.filed = value

    db.commit()
    db.refresh(tenant)

    log_audit_event(db , action="tenant.update", resource=f"tenant:{str(tenant.id)}", request=request)

    return tenant

@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(tenant_id: UUID, request: Request, db: Session = Depends(get_db)):

    require_tenant_admin(db, request.state.user_id, tenant_id)
    user_id = request.state.user_id

    tenant = db.query(TenantModel).filter(
        TenantModel.id == tenant_id,
        TenantModel.is_deleted == False
    ).first()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found!!!"
        ) 
    
    membership = db.query(TenantMembershipModel).filter(
        TenantMembershipModel.user_id == user_id,
        TenantMembershipModel.tenant_id == tenant_id
    ).first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this tenant!!!"
        )
    
    tenant.is_deleted = True

    db.commit()
    log_audit_event(db , action="tenant.delete", resource=f"role:{str(tenant.id)}", request=request)
    return

@router.post("/{tenant_id}/invite", response_model=InviteResponse)
async def invite_user(tenant_id: UUID, payload: InviteUserRequest, request: Request, db: Session = Depends(get_db)):
    
    require_tenant_admin(db, request.state.user_id, tenant_id)

    user = db.query(UserModel).filter(
        UserModel.email == payload.email
    ).first()

    if not user:
        raise HTTPException(404, "User does not exist")

    existing_membership = db.query(TenantMembershipModel).filter_by(
        user_id=user.id,
        tenant_id=tenant_id
    ).first()

    if existing_membership:
        raise HTTPException(409, "User already belongs to tenant")

    existing_invite = db.query(
        AdminInviteModel
        ).filter_by(
            user_id=user.id,
            tenant_id=tenant_id,
            status="PENDING"
        ).first()

    if existing_invite:
        raise HTTPException(409, "Invite already pending")

    invite = AdminInviteModel(
        user_id=user.id,
        tenant_id=tenant_id,
        role=payload.role,
        invited_by=request.state.user_id
    )

    db.add(invite)
    db.commit()
    db.refresh(invite)

    log_audit_event(db , action="membership.update_role", resource=f"user:{str(user.id)}", request=request)

    return {
        "invite_id": invite.id,
        "tenant_id": tenant_id,
        "user_id": user.id,
        "role": invite.role,
        "status": invite.status
    }

@router.get("/{tenant_id}/users", response_model=ListTenantUsersResponse, status_code=status.HTTP_200_OK)
def list_tenant_users(tenant_id: UUID, request: Request, db: Session = Depends(get_db)):
    membership = db.query(
        TenantMembershipModel
    ).filter(
        TenantMembershipModel.user_id==request.state.user_id,
        TenantMembershipModel.tenant_id==tenant_id
    ).first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not a member of this tenant!!!"
        )
    
    members = db.query(
        TenantMembershipModel
    ).filter(
        TenantMembershipModel.tenant_id==tenant_id
    ).all()

    return {
        "tenant_id": str(tenant_id),
        "count": len(members),
        "users": [
            {
                "user_id": str(m.user.id),
                "email": m.user.email,
                "name": m.user.name,
                "role": m.role,
                "joined_at": m.joined_at
            }
            for m in members
        ]
    }

@router.put("/users/{user_id}/role", response_model=UpdateUserRoleResponse, status_code=status.HTTP_200_OK)
async def update_user_role(user_id: UUID, payload: UpdateUserRoleRequest, request: Request, db: Session = Depends(get_db)):
    tenant_id = payload.tenant_id
    new_role = payload.new_role

    require_tenant_admin(db, request.state.user_id, tenant_id)

    membership = db.query(TenantMembershipModel).filter_by(
        user_id=user_id,
        tenant_id=tenant_id
    ).first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not in tenant"
            )

    membership.role = new_role
    db.commit()

    log_audit_event(db , action="membership.change_role", resource=f"user:{str(user_id)}", request=request)

    return {
        "status": "updated",
        "user_id": str(user_id),
        "tenant_id": str(tenant_id),
        "new_role": new_role
    }

@router.delete("/users/{user_id}", response_model=RemoveUserResponse, status_code=status.HTTP_200_OK)
async def remove_user_from_tenant( user_id: UUID, tenant_id: UUID, request: Request, db: Session = Depends(get_db)):
    require_tenant_admin(db, request.state.user_id, tenant_id)

    membership = db.query(TenantMembershipModel).filter_by(
        user_id=user_id,
        tenant_id=tenant_id
    ).first()

    if not membership:
        raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found in tenant"
            )

    db.delete(membership)
    db.commit()

    log_audit_event(db , action="membership.remove", resource=f"role:{str(user_id)}", request=request)

    return {
        "status": "removed",
        "user_id": str(user_id),
        "tenant_id": str(tenant_id)
    }
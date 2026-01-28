from uuid import UUID
from typing import List
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, status, Request

from src.db.session import get_db
from src.models.user import Users as UserModel
from src.models.tenant import Tenant as TenantModel
from src.core.security import create_access_token, oauth2_scheme
from src.models.tenantMembership import TenantMembership as TenantMembershipModel
from src.schemas.tenants_schema import TenantCreate as TenantCreateSchema, TenantPublic, TenantSummary, TenantSwitchRequest, TenantUpdate

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

@router.get("/my", response_model=List[TenantSummary], status_code=status.HTTP_200_OK)
def get_my_tenants(request: Request, db: Session = Depends(get_db)):

    user_id = request.state.user_id

    memberships = db.query(
        TenantMembershipModel
    ).filter(
        TenantMembershipModel.user_id == user_id
    ).all()

    if not memberships:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cant find any tenants under this user!!!"
        )

    return [
        {
            "id": m.id,
            "name": m.tenant.name,
            "role": m.role
        }

        for m in memberships
    ]

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

    return {
        "id": tenant.id,
        "name": tenant.name,
        "owner_id": membership.user_id,
        "created_at": tenant.created_at,
        "role": membership.role
    }


@router.patch("/{tenant_id}", status_code=status.HTTP_200_OK)
async def update_tenant(request: Request, tenant_id: UUID, update: TenantUpdate, db: Session = Depends(get_db)):
    
    if request.state.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only tenant admin can update this tenant!!!"
        )

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

    return tenant



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
        user=request.state.user_id,
        tenant_id=str(membership.tenant_id),
        role=membership.role
    )

    return {
        "access_token": new_token,
        "tenant_id": str(membership.tenant_id),
        "role": membership.role
    }

@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(tenant_id: UUID, request: Request, db: Session = Depends(get_db)):

    if request.state.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only tenant owner can delete this tenant!!!"
        )

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

    return
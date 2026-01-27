from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, status, Request

from src.db.session import get_db
from src.core.security import oauth2_scheme
from src.models.user import Users as UserModel
from src.models.tenant import Tenant as TenantModel
from src.schemas.tenants_schema import TenantCreate as TenantCreateSchema
from src.models.tenantMembership import TenantMembership as TenantMembershipModel

router = APIRouter(
    prefix="/tenants", 
    tags=["Tenants"],
    dependencies=[Depends(oauth2_scheme)]
)

@router.post("/create")
async def create_tenant(payload: TenantCreateSchema, request: Request, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):

    user_id = request.state.user_id

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Unauthorized!!!"
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
    await db.commit()
    await db.refresh(tenant)

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
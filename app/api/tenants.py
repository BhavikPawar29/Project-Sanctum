from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.database_connection import get_db
from app.models.Tenant import Tenant as TenantModel
from app.schemas.tenants_schema import Tenant as TenantSchema

router = APIRouter(
    prefix="/tenants", 
    tags=["Tenants"]
    #dependencies=[Depends(oauth2_scheme)]
)

@router.post("/create")
async def create_tenant(payload: TenantSchema, db: Session = Depends(get_db)):
    
    existing = db.query(
            TenantModel
        ).filter(
            TenantModel.name == payload.name
        ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
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
    }
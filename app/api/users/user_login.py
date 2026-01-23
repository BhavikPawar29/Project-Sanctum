from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.database_connection import get_db
from app.models.User import Users as UserModel
from app.models.TenantMembership import TenantMembership as TenantMembershipModel
from app.core.security import verify_password, create_access_token

router = APIRouter(
    prefix="/users", 
    tags=["Users"]
    )


@router.post("/login", status_code=status.HTTP_200_OK)
async def login (form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    
    db_user = db.query(
        UserModel
    ).filter(
        UserModel.email == form_data.username 
    ).first()

    if not db_user or not verify_password(form_data.password, db_user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid credentials!!!"
        )
    
    membership = db.query(TenantMembershipModel).filter(
        TenantMembershipModel.user_id == db_user.id
    ).first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not belong to nay tenant!!!"
        )
    
    token = create_access_token(
        user=db_user,
        tenant_id=str(membership.tenant_id),
        role=membership.role
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }

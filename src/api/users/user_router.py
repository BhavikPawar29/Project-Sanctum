import os
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_login import LoginManager
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.models.user import Users as UserModel
from src.models.tenantMembership import TenantMembership as TenantMembershipModel
from src.core.security import create_refresh_token, hash_password, verify_password, create_access_token
from src.schemas.auth_schema import RegisterRequest, TokenResponse

router = APIRouter(
    prefix="/users", 
    tags=["Users"]
    )

def _load_user(db: Session, email: str):
    return db.query(
            UserModel
        ).filter(
            UserModel.email == email
        ).first()


@router.post("/login", status_code=status.HTTP_200_OK)
async def login (form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    
    db_user = _load_user(db, form_data.username)

    if not db_user or not verify_password(form_data.password, db_user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid credentials!!!"
        )
    
    membership = db.query(TenantMembershipModel).filter(
        TenantMembershipModel.user_id == db_user.id
    ).first()

    if membership:
        token = create_access_token(
            user=db_user,
            tenant_id=str(membership.tenant_id),
            role=membership.role
        )
    else:
        token = create_access_token(user=db_user) 

    return {
        "access_token": token,
        "token_type": "bearer"
    }

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, db: Session = Depends(get_db)):
    
    existing = _load_user(db, data.email)

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email Already Exists!!!"
        )

    user = UserModel(
        email=data.email,
        password=hash_password(data.password),
        name=data.name
    )


    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user=user)
    refresh_token = create_refresh_token(user)

    return {
        "access_token": token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user_id": str(user.id)
    }

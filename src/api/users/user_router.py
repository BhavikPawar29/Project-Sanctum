from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import APIRouter, Depends, HTTPException, Request, status

from src.db.session import get_db
from src.core.security import create_password_reset_token, oauth2_scheme
from src.models.user import Users as UserModel
from src.schemas.auth_schema import ForgotPasswordRequest, RegisterRequest, ResetPasswordRequest, TokenResponse
from src.models.tenantMembership import TenantMembership as TenantMembershipModel
from src.services.redis_tokens import get_refresh_token, revoke_refresh_token, store_refresh_token
from src.core.security import create_refresh_token, decode_token, hash_password, verify_password, create_access_token

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

    refresh_token = create_refresh_token(user=db_user)

    store_refresh_token(db_user.id, refresh_token)

    return {
        "access_token": token,
        "refresh_token": refresh_token,
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
    refresh_token = create_refresh_token(user=user)

    store_refresh_token(user.id, refresh_token)

    return {
        "access_token": token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user_id": str(user.id)
    }

@router.post("/refresh")
async def refresh_token(refresh_token: str, db: Session = Depends(get_db)):

    payload = decode_token(refresh_token, expected_type="refresh")

    user_id = payload["sub"]

    stored = get_refresh_token(user_id)
    if stored != refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Refresh token revoked!!!")

    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail= "User not found")

    membership = db.query(TenantMembershipModel).filter(
        TenantMembershipModel.user_id == user.id
    ).first()

    tenant_id = str(membership.tenant_id) if membership else None
    role = membership.role if membership else None

    new_access = create_access_token(user, tenant_id, role)
    new_refresh = create_refresh_token(user)

    store_refresh_token(user_id, new_refresh)

    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer"
    }

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


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    user = db.query(UserModel).filter(UserModel.email == data.email).first()

    if not user:
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail= {"message": "If account exists, reset link sent"}
        )

    reset_token = create_password_reset_token(str(user.id))

    print(f"PASSWORD RESET TOKEN: {reset_token}")

    return {"message": "Reset link sent"}

@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):

    payload = decode_token(data.token, expected_type="password_reset")
    user_id = payload.get("sub")

    user = db.query(UserModel).filter(UserModel.id == user_id).first()

    if not user:
        raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="User not found"
            )

    user.password = hash_password(data.new_password)

    db.commit()

    return {"message": "Password reset successful"}


@router.post("/logout")
async def logout(request: Request, token: str = Depends(oauth2_scheme)):
    user_id = request.state.user_id
    revoke_refresh_token(str(user_id))
    return {"message": "Logged out successfully"}


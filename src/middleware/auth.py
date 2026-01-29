from jose import JWTError
from fastapi import Request, status

from fastapi.responses import JSONResponse
from src.core.security import decode_token

from sqlalchemy.orm import Session
from src.db.session import SessionLocal
from src.models.rbac import Role as RoleModel, Permission as PermissionModel, RolePermission as RolePermissionModel

#import logging


PUBLIC_PATHS = {
    "/users/login",
    "/users/register",
    "/users/refresh",
    "/users/forgot-password",
    "/users/reset-password",
    "/docs",
    "/openapi.json",
    "/docs/oauth2-redirect",
    "/media/"
}
async def auth_middleware(request: Request, call_next):
    
    path = request.url.path

    if any(path.startswith(p) for p in PUBLIC_PATHS):
        return await call_next(request)
    
    auth_header = request.headers.get("Authorization")

    #print(f"auth_header {auth_header}")

    if not auth_header:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Missing Authorization Header!!!"}
        )
    
    
    if not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            content={"detail": "Invalid token type!!!"}
        )

    token = auth_header.split(" ")[1]

    if not token:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail":"Bearer token missing!!!"}
        )
    
    try:
        payload = decode_token(token, expected_type="access")

        #print(f"JWT PAYLOAD: {payload}")

        if payload.get("type") != "access":
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid token"}
            )

        user_id = payload.get("sub")
        role_name = payload.get("role")
        tenant_id = payload.get("tenant_id")

        if not user_id:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid token payload"}
            )

    except JWTError:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Invalid or expired token"}
        )
    
    db: Session = SessionLocal()
    permissions = []

    try:
        role = db.query(RoleModel).filter_by(
            r_name=role_name,
            tenant_id=tenant_id
        ).first()

        if role:
            perms = db.query(PermissionModel.code).join(
                RolePermissionModel,
                RolePermissionModel.permission_id == PermissionModel.id
            ).filter(
                RolePermissionModel.role_id == role.id
            ).all()

            permissions = [p[0] for p in perms]

    finally:
        db.close()

    request.state.user_id = user_id
    request.state.role = role_name
    request.state.permissions = permissions
    request.state.tenant_id = tenant_id

    response = await call_next(request)
    return response

from fastapi import Request, status
from jose import jwt, JWTError
from fastapi.responses import JSONResponse
from app.core.security import SECRET_KEY, ALGORITHM
import logging


PUBLIC_PATHS = {
    "/users/login",
    "/auth/register",
    "/auth/refresh",
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
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        print(f"JWT PAYLOAD: {payload}")

        if payload.get("type") != "access":
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid token"}
            )

        user_id = payload.get("sub")
        role = payload.get("role")
        tenant_id = payload.get("tenant_id")

        if not user_id or not role:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid token payload"}
            )

    except JWTError:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Invalid or expired token"}
        )

    request.state.user_id = user_id
    request.state.role = role
    request.state.tenant_id = tenant_id

    response = await call_next(request)
    return response
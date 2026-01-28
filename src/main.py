from fastapi import FastAPI
from src.api.tenants import tenants_router
from src.api.users import user_router
from src.api.rbac import rbac_routes 
from starlette.middleware.base import BaseHTTPMiddleware

from src.middleware.auth import auth_middleware

app = FastAPI(
    title="Sanctum"
    )

app.include_router(tenants_router.router)
app.include_router(user_router.router)
app.include_router(rbac_routes.router)

app.add_middleware(
    BaseHTTPMiddleware,
    dispatch=auth_middleware
)
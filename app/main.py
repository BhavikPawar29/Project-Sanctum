from fastapi import FastAPI
from app.api import tenants
from app.api.users import user_login
from starlette.middleware.base import BaseHTTPMiddleware

from app.middleware.auth import auth_middleware

app = FastAPI(
    title="Sanctum"
    )

app.include_router(tenants.router)
app.include_router(user_login.router)

app.add_middleware(
    BaseHTTPMiddleware,
    dispatch=auth_middleware
)
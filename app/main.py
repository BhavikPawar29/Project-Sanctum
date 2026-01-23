from fastapi import FastAPI
#from routes import tenants
from app.routes import tenants

app = FastAPI(
    title="Sanctum"
    )

app.include_router(tenants.router)

import os
from dotenv import load_dotenv
load_dotenv()

from src.db.session import engine, Base

# Import ALL models
from src.models.user import *
from src.models.tenant import *
from src.models.tenantMembership import *
from src.models.projects import *
from src.models.rbac import *
from src.models.auditLog import *
from src.models.adminInvites import *
from src.models.memberRequest import *

print("Creating tables...")
Base.metadata.create_all(bind=engine)
print("Done!")
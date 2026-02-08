from sqlalchemy.orm import Session
from src.models.auditLog import AuditLog


def log_audit_event(db: Session, action: str, resource: str, request=None, tenant_id=None, user_id=None):
    ip_address = None

    if request:
        ip_address = request.client.host if request.client else None

        tenant_id = tenant_id or getattr(request.state, "tenant_id", None)
        user_id = user_id or getattr(request.state, "user_id", None)

    audit = AuditLog(
        tenant_id=tenant_id,
        user_id=user_id,
        action=action,
        resource=resource,
        ip_address=ip_address
    )

    db.add(audit)
    db.commit()

    return

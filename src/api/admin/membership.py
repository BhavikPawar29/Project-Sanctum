from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from src.core.security import oauth2_scheme
from src.db.session import get_db
from src.models.memberRequest import MemberRequest as MemberRequestModel
from src.schemas.membership_schema import ApproveRequestSchema, RejectRequestSchema
from src.services.membership_service import approve_request, reject_request
from src.services.membership_service import require_tenant_admin

router = APIRouter(
    prefix="/membership",
    tags=["Membership Requests"],
    dependencies=[Depends(oauth2_scheme)]
)


@router.get("/tenant/{tenant_id}/requests", status_code=status.HTTP_200_OK)
def list_tenant_requests(tenant_id: UUID, request: Request, db: Session = Depends(get_db)):
    require_tenant_admin(db, request.state.user_id, tenant_id)

    requests = db.query(MemberRequestModel).filter(
        MemberRequestModel.tenant_id == tenant_id,
        MemberRequestModel.status == "PENDING"
    ).all()

    return [
        {
            "request_id": r.id,
            "user_id": r.user_id,
            "status": r.status,
            "requested_at": r.requested_at
        }
        for r in requests
    ]


@router.post("/requests/{request_id}/approve", status_code=status.HTTP_201_CREATED)
def approve_membership_request(request_id: UUID, payload: ApproveRequestSchema, request: Request, db: Session = Depends(get_db)):
    req = db.query(
        MemberRequestModel
        ).filter_by(
            id=request_id
        ).first()

    if not req:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found!!!"
        )

    if req.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Request already processed!!!"
        )
    
    require_tenant_admin(db, request.state.user_id, req.tenant_id)

    updated = approve_request(
        db=db,
        req=req,
        admin_id=request.state.user_id,
        note=payload.note
    )

    return {
        "status": updated.status,
        "tenant_id": updated.tenant_id,
        "user_id": updated.user_id
    }

@router.post("/requests/{request_id}/reject", status_code=status.HTTP_200_OK)
def reject_membership_request(request_id: UUID, payload: RejectRequestSchema, request: Request, db: Session = Depends(get_db)):
    req = db.query(MemberRequestModel).filter_by(id=request_id).first()

    if not req:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found!!!"
        )

    if req.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Request already processed!!!"
        )

    require_tenant_admin(db, request.state.user_id, req.tenant_id)

    updated = reject_request(
        db=db,
        req=req,
        admin_id=request.state.user_id,
        note=payload.note
    )

    return {
        "status": updated.status,
        "note": updated.note
    }

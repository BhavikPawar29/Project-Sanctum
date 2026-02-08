from uuid import UUID
from src.services.audit_service import log_audit_event
from src.db.session import get_db
from sqlalchemy.orm import Session
from src.core.security import oauth2_scheme
from src.schemas.role_schema import AssignRoleRequest, RoleCreate, RoleUpdate
from fastapi import APIRouter, Depends, HTTPException, Request, status
from src.models.rbac import Permission as PermissionModel, Role as RoleModel, RolePermission as RolePermissionModel, UserRole as UserRoleModel

router = APIRouter(
    prefix="/roles", 
    tags=["Roles (Admin/Owner)"],
    dependencies=[Depends(oauth2_scheme)]
)

@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_role(data: RoleCreate, request: Request, db: Session = Depends(get_db)):
    
    if "role.create" not in request.state.permissions:
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied!!!"
        )

    role = RoleModel(
        r_name=data.name,
        tenant_id=request.state.tenant_id
    )
    
    if not role: 
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not created!!!"
        )
    
    db.add(role)
    db.flush()

    perms = db.query(
        PermissionModel
    ).filter(
        PermissionModel.code.in_(data.permissions)
    ).all()


    for p in perms:
        db.add(RolePermissionModel
            (
            role_id=role.id, 
            permission_id=p.id
            )
        )

    db.commit()
    log_audit_event(db , action="role.create", resource=f"role:{role.id}", request=request)
    
    return {
        "role_id": 
        role.id
        }

@router.get("/list", status_code=status.HTTP_200_OK)
def list_roles(request: Request, db: Session = Depends(get_db)):

    if "role.view" not in request.state.permissions:
        raise HTTPException(
            status_code=403,
            detail="Access denied!!!"
        )
    
    roles = db.query(RoleModel).filter(
        RoleModel.tenant_id == request.state.tenant_id
    ).all()

    return roles

@router.patch("/{role_id}", status_code=status.HTTP_200_OK)
async def update_role(role_id: UUID, update: RoleUpdate, request: Request, db: Session = Depends(get_db)):
    
    if "role.create" not in request.state.permissions:
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied!!!"
        )

    role = db.query(
        RoleModel
    ).filter(
        RoleModel.id == role_id,
        RoleModel.tenant_id == request.state.tenant_id
    ).first()

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found!!!"
        )
    
    if not update.r_name and update.permissions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No data provided for update!!!"
        )
    
    if update.r_name:
        role.r_name = update.r_name

    if update.permissions:
        db.query(
            RolePermissionModel
        ).filter_by(
            role_id=role.id
        ).delete()


        perms = db.query(PermissionModel).filter(
                PermissionModel.code.in_(update.permissions)
            ).all()

        for p in perms:
            db.add(
                RolePermissionModel(
                    role_id=role.id, 
                    permission_id=p.id
                    )
                )
        
    db.commit()
    log_audit_event(db , action="role.update", resource=f"role:{role.id}", request=request)

    return {
        "status": "Updated"
    }

@router.delete("/{role_id}")
def delete_role(role_id: UUID, request: Request, db: Session = Depends(get_db)):

    if "role.delete" not in request.state.permissions:
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied!!!"
        )

    role = db.query(RoleModel).filter_by(
        id=role_id,
        tenant_id=request.state.tenant_id
    ).first()

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found!!!"
        )

    db.delete(role)
    db.commit()

    log_audit_event(db , action="role.delete", resource=f"role:{role.id}", request=request)

    return {
        "status": "deleted"
        }

@router.post("/assign-user")
def assign_role(data: AssignRoleRequest, request: Request, db: Session = Depends(get_db)):
    
    if "role.assign" not in request.state.permissions:
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied!!!"
        )

    role = db.query(RoleModel).filter_by(
        id=data.role_id,
        tenant_id=request.state.tenant_id
    ).first()

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
            )

    assignment = UserRoleModel(
        user_id=data.user_id,
        role_id=role.id,
        tenant_id=request.state.tenant_id
    )

    db.merge(assignment)
    db.commit()

    log_audit_event(db , action="role.assign", resource=f"user:{data.user_id}", request=request)

    return {
        "status": "assigned"
        }

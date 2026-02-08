from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List

from db.transactions import transactional
from src.services.audit_service import log_audit_event
from src.db.session import get_db
from src.models.projects import Project as ProjectModel
from src.schemas.project_schema import ProjectCreate, ProjectUpdate, ProjectResponse
from src.services.membership_service import require_permission
from src.core.security import oauth2_scheme

router = APIRouter(
    prefix="/projects",
    tags=["Projects"],
    dependencies=[Depends(oauth2_scheme)]
)

@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate,request: Request ,ctx = Depends(require_permission("project.create")), db: Session = Depends(get_db)):
    project = ProjectModel(
        tenant_id=ctx.tenant_id,
        name=payload.name,
        description=payload.description,
        created_by=ctx.user_id
    )

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not created!!!"
        )

    with transactional(db):

        db.add(project)
        db.flush()
        db.refresh(project)

        log_audit_event(
            db,
            action="project.create",
            resource=f"project:{str(project.id)}",
            request=request
        )

    return project


@router.get("", response_model=List[ProjectResponse])
def list_projects(ctx = Depends(require_permission("project.view")), db: Session = Depends(get_db)):
    
    projects = db.query(ProjectModel).filter(
        ProjectModel.tenant_id == ctx.tenant_id
    ).all()

    return projects


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: UUID, ctx = Depends(require_permission("project.view")), db: Session = Depends(get_db)):
    
    project = db.query(ProjectModel).filter(
        ProjectModel.id == project_id,
        ProjectModel.tenant_id == ctx.tenant_id
    ).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found!!!"
        )

    return project


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(project_id: UUID, request: Request, payload: ProjectUpdate, ctx = Depends(require_permission("project.update")), db: Session = Depends(get_db)):
    
    project = db.query(ProjectModel).filter(
        ProjectModel.id == project_id,
        ProjectModel.tenant_id == ctx.tenant_id
    ).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found!!!"
        )

    with transactional():
        update_data = payload.dict(exclude_unset=True)

        for key, value in update_data.items():
            setattr(project, key, value)

        db.flush()
        db.refresh(project)

        log_audit_event(
            db, 
            action="project.update", 
            resource=f"project:{str(project.id)}", 
            request=request
        )

    return project


@router.delete("/{project_id}")
def delete_project(project_id: UUID, request: Request, ctx = Depends(require_permission("project.delete")), db: Session = Depends(get_db)):
    
    project = db.query(ProjectModel).filter(
        ProjectModel.id == project_id,
        ProjectModel.tenant_id == ctx.tenant_id
    ).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found!!!"
        )

    with transactional(db):
        db.delete(project)

        log_audit_event(
            db, 
            action="project.deleted", 
            resource=f"project:{str(project.id)}", 
            request=request
        )

    return {
        "status": "deleted"
        }

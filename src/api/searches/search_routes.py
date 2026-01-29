from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.schemas.search_schema import AdvancedSearchRequest
from src.services.search_service import basic_search, advanced_search
from src.core.security import oauth2_scheme

router = APIRouter(
    prefix="/search",
    tags=["Search"],
    dependencies=[Depends(oauth2_scheme)]
)


@router.get("", status_code=status.HTTP_200_OK)
def search(q: str, request: Request, db: Session = Depends(get_db)):

    tenant_id = request.state.tenant_id
    user_id = request.state.user_id

    if not q or len(q.strip()) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query too short!!!"
        )

    results = basic_search(db, tenant_id, user_id, q)

    return {
        "query": q,
        "count": len(results),
        "results": results
    }


@router.post("/advanced", status_code=status.HTTP_200_OK)
def search_advanced(payload: AdvancedSearchRequest, request: Request, db: Session = Depends(get_db)):

    tenant_id = request.state.tenant_id
    user_id = request.state.user_id

    results = advanced_search(db, tenant_id, user_id, payload)

    return {
        "filters": payload.dict(),
        "count": len(results),
        "results": results
    }

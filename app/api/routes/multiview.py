"""Blueprint Multiview API."""

from fastapi import APIRouter, Request, Response

from app.api.depends import SessionDep
from app.models import MultiviewCreate, MultiviewPublic, Multiviews, MultiviewUpdate

router = APIRouter()


@router.get("/")
async def get(session: SessionDep) -> list[MultiviewPublic]:
    """List hosts."""
    return session.get_all(Multiviews)


@router.post("/", status_code=204)
async def post(session: SessionDep, multiview: MultiviewCreate, request: Request):
    """Create host."""
    db_multiview = Multiviews.model_validate(multiview)
    session.add(db_multiview)
    session.commit()
    session.refresh(db_multiview)
    return Response(headers={"Location": f"{request.url._url}{db_multiview.id}"})


@router.get("/{id}")
async def get_multiview(session: SessionDep, id: int) -> MultiviewPublic:
    """Get multiview."""
    return session.get_or_404(Multiviews, id, error_desc="View not found")


@router.put("/{id}", status_code=204)
async def put_multiview(session: SessionDep, multiview: MultiviewUpdate, id: int):
    """Set multiview."""
    db_multiview = session.get_or_404(Multiviews, id, error_desc="View not found")
    db_multiview.sqlmodel_update(multiview)
    session.add(db_multiview)
    session.commit()


@router.delete("/{id}", status_code=204)
async def delete_multiview(session: SessionDep, id: int):
    """Delete multiview."""
    db_multiview = session.get_or_404(Multiviews, id, error_desc="View not found")
    session.delete(db_multiview)
    session.commit()

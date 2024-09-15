"""Blueprint Buttons API."""

from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.depends import SessionDep
from app.models import ButtonCreate, ButtonPublic, Buttons, ButtonUpdate

router = APIRouter()


@router.get("/")
async def get_buttons(session: SessionDep) -> list[ButtonPublic]:
    """List buttons."""
    return session.get_all(Buttons)


@router.post("/", status_code=204)
async def post_buttons(session: SessionDep, button: ButtonCreate, request: Request):
    """Create button."""
    button = Buttons.model_validate(button)
    session.add(button)
    session.commit()
    session.refresh(button)
    return Response(headers={"Location": f"{request.url._url}{button.id}"})


@router.get("/{id}")
async def get(session: SessionDep, id: int) -> ButtonPublic:
    """Get button."""
    return session.get_or_404(Buttons, id, error_desc="Button not found")


@router.put("/{id}", status_code=204)
async def put(session: SessionDep, button: ButtonUpdate, id: int):
    """Set button."""
    db_button = session.get_or_404(Buttons, id, error_desc="Button not found")
    db_button.sqlmodel_update(button)
    session.add(db_button)
    session.commit()


@router.delete("/{id}", status_code=204)
async def delete(session: SessionDep, id: int):
    """Delete button."""
    db_button = session.get_or_404(Buttons, id, error_desc="Button not found")
    session.delete(db_button)
    session.commit()

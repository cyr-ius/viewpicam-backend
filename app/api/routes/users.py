"""Blueprint Users API."""

from fastapi import APIRouter, Request, Response
from sqlalchemy import select

from app.api.depends import SessionDep
from app.core.config import Locale
from app.core.security import hash_password
from app.models import User, UserCreate, UserPublic, UserUpdate

router = APIRouter()


@router.get("/")
async def get(session: SessionDep) -> list[UserPublic]:
    """List users."""
    return session.execute(select(User).filter(User.id > 0)).scalars().all()


@router.post("/", status_code=204)
async def post(session: SessionDep, user: UserCreate, request: Request):
    """Create user."""
    hashed_password = hash_password(user.password)
    db_user = User.model_validate(user, update={"secret": hashed_password})
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return Response(headers={"Location": f"{request.url._url}{db_user.id}"})


@router.put("/{id}/locale", status_code=204)
async def put_locale(session: SessionDep, locale: Locale, id: int):
    """Set language."""
    db_user = session.get_or_404(User, id, error_desc="User not found")
    db_user.sqlmodel_update(locale)
    session.add(db_user)
    session.commit()


@router.get("/{id}")
async def get_user(session: SessionDep, id: int) -> UserPublic:
    """Get user."""
    return session.get_or_404(User, id, error_desc="User not found")


@router.put("/{id}", status_code=204)
async def put_user(session: SessionDep, user: UserUpdate, id: int):
    """Set user."""
    db_user = session.get_or_404(User, id, error_desc="User not found")
    user_data = user.model_dump(exclude_unset=True)

    extra = {}
    if user.password:
        extra.update({"secret": hash_password(user.password)})

    db_user.sqlmodel_update(user_data, update=extra)
    session.add(db_user)
    session.commit()


@router.delete("/{id}", status_code=204)
async def delete_user(session: SessionDep, id: int):
    """Delete user."""
    db_user = session.get_or_404(User, id, error_desc="User not found")
    session.delete(db_user)
    session.commit()

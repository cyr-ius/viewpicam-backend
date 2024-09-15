from collections.abc import Generator
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyCookie, HTTPBearer
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import config
from app.core.db import engine
from app.core.security import ALGORITHM
from app.models import TokenPayload, User


def get_or_404(self, Table, id, *, error_desc: str | None = None):
    """Get by id or return 404"""
    item = self.execute(select(Table).filter_by(id=id)).scalars().first()
    if item is None:
        raise HTTPException(404, error_desc)
    return item


def get_all(self, Table, *, error_desc: str | None = None):
    """Get by id or return 404"""
    item = self.execute(select(Table)).scalars().all()
    if item is None:
        raise HTTPException(404, error_desc)
    return item


def get_db() -> Generator[Session, None, None]:
    Session.get_or_404 = get_or_404
    Session.get_all = get_all
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]


def get_session():
    Session = sessionmaker(bind=engine)
    return Session


async def protected(
    key_result=Depends(APIKeyCookie(name="x-api-key", auto_error=False)),
    jwt_result=Depends(HTTPBearer(auto_error=False)),
):
    if not (key_result or jwt_result):
        raise HTTPException(status_code=403, detail="Not authenticated")

    return key_result or jwt_result


TokenDep = Annotated[str, Security(protected)]


def get_current_user(session: SessionDep, token: TokenDep) -> User:
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[ALGORITHM])
        token_data = TokenPayload(**payload)
    except (InvalidTokenError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    user = session.get(User, token_data.id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.enabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_current_active_superuser(current_user: CurrentUser) -> User:
    if not current_user.right == 8:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user


def check_superuser_exists(session: SessionDep) -> bool:
    search = session.execute(select(User).filter(User.right == 8)).scalars().first()
    return search is not None


CheckSuperUser = Annotated[bool, Depends(check_superuser_exists)]

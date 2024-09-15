"""Blueprint Authorize API."""

from __future__ import annotations

import random
from datetime import datetime as dt
from datetime import timezone

import jwt
from fastapi import (
    APIRouter,
    HTTPException,
    Response,
    status,
)
from pyotp import TOTP
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from app.api.depends import CheckSuperUser, CurrentUser, SessionDep
from app.core.config import config
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.models import ApiToken, CameraToken, Login, Register, TokenInfo, User

router = APIRouter()

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

authorize_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="User or password incorrect",
    headers={"WWW-Authenticate": "Bearer"},
)

inactive_exception = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
)

otp_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user"
)

already_exists = HTTPException(
    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    detail="User name is already exists",
)


@router.post("/authorize", status_code=200)
async def authorize(
    session: SessionDep, login: Login, response: Response
) -> TokenInfo | str:
    user = session.exec(select(User).filter_by(name=login.username)).first()

    if user is None or user.enabled is False:
        raise authorize_exception

    if verify_password(login.password, user.secret) is False:
        raise authorize_exception

    if user.otp_confirmed and login.otp_code is None:
        response.status_code = 202
        return "OTP Required"
    elif user.otp_confirmed and TOTP(user.otp_secret).verify(login.otp_code) is False:
        raise otp_exception

    jwtoken, expires_in = create_access_token(
        user.name, id=user.id, otp_confirmed=(user.otp_confirmed == 1)
    )

    response.set_cookie(
        "x-api-key",
        jwtoken,
        secure=True,
        httponly=True,
        samesite="strict",
        expires=expires_in,
    )
    return {
        "access_token": jwtoken,
        "token_type": "Bearer",
        "expires_in": int(expires_in.timestamp() - dt.now().timestamp()),
    }


@router.get("/userinfo")
async def read_users_me(current_user: CurrentUser) -> User:
    return current_user


@router.get("/firstenrollment", status_code=204)
async def check_first_run(
    session: SessionDep, exists: CheckSuperUser, response: Response
):
    if exists:
        response.status_code = 202
        return


@router.get("/healthcheck", status_code=204)
async def health_check():
    pass


@router.post("/register", status_code=204)
async def register_user(
    session: SessionDep, exists: CheckSuperUser, register: Register
):
    """Register first account."""

    if exists:
        raise HTTPException(422, "Registration already done !")

    if (password := register.password) != register.password_2:
        raise HTTPException(422, "Password mismatch.")

    try:
        registered_user = {
            "name": register.username,
            "secret": hash_password(password),
            "right": config.USERLEVEL["max"],
        }
        db_user = User.model_validate(registered_user)
        session.add(db_user)
        session.commit()
        session.refresh(db_user)

    except IntegrityError:
        raise already_exists


@router.get("/logout", status_code=204, operation_id="idp-get-logout")
@router.post("/logout", status_code=204, operation_id="idp-post-logout")
async def logout(response: Response):
    """Logout user and clean secure cookie"""
    response.set_cookie("x-api-key", "", expires=0)


@router.get("/camera_token")
async def get_cam_token(session: SessionDep, current_user: CurrentUser) -> CameraToken:
    """Get camera token."""
    db_user = session.get(User, current_user.id)
    return db_user


@router.post("/camera_token", status_code=204)
async def post_cam_token(session: SessionDep, current_user: CurrentUser):
    """Create camera token."""
    db_user = session.get(User, current_user.id)
    db_user.sqlmodel_update({"cam_token": f"B{random.getrandbits(256)}"})
    session.add(db_user)
    session.commit()


@router.delete("/camera_token", status_code=204)
async def delete_cam_token(session: SessionDep, current_user: CurrentUser):
    """Delete camera token."""
    db_user = session.get(User, current_user.id)
    db_user.sqlmodel_update({"cam_token": None})
    session.add(db_user)
    session.commit()


@router.get("/token")
async def get_api_token(session: SessionDep, current_user: CurrentUser) -> ApiToken:
    """Get token."""
    db_user = session.get(User, current_user.id)
    return db_user


@router.post("/token", status_code=204)
async def post_api_token(session: SessionDep, current_user: CurrentUser):
    """Create token."""
    db_user = session.get(User, current_user.id)
    api_token = jwt.encode(
        payload={
            "iss": "ViewPiCam",
            "sub": "system",
            "id": 1,
            "iat": dt.now(tz=timezone.utc),
        },
        key=config.SECRET_KEY,
        algorithm="HS256",
    )
    db_user.sqlmodel_update({"api_token": api_token})
    session.add(db_user)
    session.commit()


@router.delete("/token", status_code=204)
async def delete_api_token(session: SessionDep, current_user: CurrentUser):
    """Delete token."""
    db_user = session.get(User, current_user.id)
    db_user.sqlmodel_update({"api_token": None})
    session.add(db_user)
    session.commit()

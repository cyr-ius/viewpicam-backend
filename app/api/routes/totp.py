"""Blueprint API."""

import pyotp
from fastapi import APIRouter, HTTPException

from app.api.depends import SessionDep
from app.models import Otp, Secret, User

router = APIRouter()


@router.get("/{id}")
async def get(session: SessionDep, id: int) -> Otp:
    """Get OTP for a user."""
    user = session.get_or_404(User, id, error_desc="User not found")
    if user.otp_confirmed is False:
        user.sqlmodel_update({"otp_secret": pyotp.random_base32()})
        session.add(user)
        session.commit()
    return user


@router.post("/{id}", status_code=204)
async def post(session: SessionDep, secret: Secret, id: int):
    """Confirmed OTP code."""
    user = session.get_or_404(User, id, error_desc="User not found")
    otp = pyotp.TOTP(user.otp_secret)
    if otp_confirmed := otp.verify(secret.secret) is False:
        raise HTTPException(422, "OTP incorrect")
    user.sqlmodel_update({"otp_confirmed": otp_confirmed})
    session.add(user)
    session.commit()


@router.delete("/{id}", status_code=204)
async def delete(session: SessionDep, id: int):
    """Delete OTP infos for a user."""
    user = session.get_or_404(User, id, error_desc="User not found")
    user.sqlmodel_update({"otp_secret": None, "otp_confirmed": False})
    session.add(user)
    session.commit()

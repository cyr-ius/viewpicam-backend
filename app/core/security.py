"""Protection and identities."""

from __future__ import annotations

from datetime import datetime as dt
from datetime import timedelta, timezone
from hashlib import scrypt

import jwt

from app.core.config import config

ALGORITHM = "HS256"


def hash_password(password):
    return scrypt(
        password.encode(), salt=config.SECRET_KEY.encode(), n=16384, r=8, p=1
    ).hex()


def verify_password(password, known_hash):
    return (
        scrypt(
            password.encode(), salt=config.SECRET_KEY.encode(), n=16384, r=8, p=1
        ).hex()
        == known_hash
    )


def create_access_token(sub, **kwargs) -> tuple[str, dt]:
    """Create JWToken."""
    dt_now = dt.now(tz=timezone.utc)
    dt_lifetime = dt_now + timedelta(minutes=config.TOKEN_LIFETIME)

    return jwt.encode(
        payload={
            "iis": "ViewPiCam",
            "sub": sub,
            "iat": dt_now,
            "exp": dt_lifetime,
            **kwargs,
        },
        key=config.SECRET_KEY,
        algorithm=ALGORITHM,
    ), dt_lifetime

"""Protection and identities."""

from __future__ import annotations

from datetime import datetime as dt
from datetime import timedelta, timezone

import jwt
from pyargon2 import hash

from app.core.config import config

ALGORITHM = "HS256"


def hash_password(password):
    return hash(password, config.SECRET_KEY)


def verify_password(password, known_hash):
    return hash(password, config.SECRET_KEY) == known_hash


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

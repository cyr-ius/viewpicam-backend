"""Protection and identities."""

from __future__ import annotations

import hashlib
from datetime import datetime as dt
from datetime import timedelta, timezone

import jwt

from app.core.config import config

ALGORITHM = "HS256"


def hash_password(password):
    salt = config.SECRET_KEY
    password_hash = hashlib.sha256((password + salt).encode("utf-8")).hexdigest()
    return password_hash


def verify_password(provided_password, stored_password):
    salt = config.SECRET_KEY
    password_hash = hashlib.sha256(
        (provided_password + salt).encode("utf-8")
    ).hexdigest()
    return password_hash == stored_password


def create_access_token(sub, **kwargs) -> (str, dt):
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

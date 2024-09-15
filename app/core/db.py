from __future__ import annotations

from sqlmodel import create_engine

from app.core.config import config

engine = create_engine(str(config.SQLALCHEMY_DATABASE_URI), echo=False)

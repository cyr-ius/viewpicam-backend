"""Read and Write settings helper."""

from __future__ import annotations

from typing import Any

from sqlmodel import Session, select

from app.core.db import engine
from app.exceptions import ViewPiCamException
from app.models import Settings


def read():
    with Session(engine) as session:
        settings = session.exec(select(Settings)).one()
        if settings is None:
            raise ViewPiCamException("Critical Exception: Settings not found.")
        return settings.data


def write(values: dict[str, Any]):
    with Session(engine) as session:
        settings = session.exec(select(Settings)).one()
        data = settings.data.copy()
        data.update(values)
        settings.sqlmodel_update({"data": data})
        session.add(settings)
        session.commit()

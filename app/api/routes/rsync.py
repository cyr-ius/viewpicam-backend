"""Api scheduler."""

from fastapi import APIRouter, HTTPException

from app.core.rsync import rsync
from app.core.settings import read, write
from app.models import Rsync

router = APIRouter()


@router.get("/")
async def get() -> Rsync:
    """Get settings."""
    return read()


@router.post("/", status_code=204)
async def post(rsync: Rsync):
    """Set settings."""
    write(rsync.model_dump())


@router.delete("/", status_code=204)
async def delete():
    """Delete settings."""
    write(Rsync.model_construct().model_dump())


@router.post("/exec", status_code=204)
async def execute_rsync():
    """Post action."""
    state = await rsync.execute()
    if state is False:
        raise HTTPException(422, "Rsync failed")

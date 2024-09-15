"""Blueprint Motion Settings API."""

from typing import Any

from fastapi import APIRouter, HTTPException

from app.core.motion import (
    MotionError,
    async_get_motion,
    async_parse_ini,
    async_restart_motion,
    async_set_motion,
    async_write_motion,
)

router = APIRouter()


@router.get("/")
async def get():
    """Get settings."""
    try:
        return await async_get_motion()
    except (ValueError, MotionError) as error:
        raise HTTPException(422, str(error))


@router.put("/", status_code=201)
async def put(motion: dict[str, Any]):
    """Set settings."""
    try:
        is_changed = False

        for key, value in motion.items():
            await async_set_motion(key, value)
            is_changed = True

        if is_changed:
            await async_write_motion()
            rsp = await async_restart_motion()
            return await async_parse_ini(rsp.text())
    except (ValueError, MotionError) as error:
        raise HTTPException(422, str(error))

    return motion

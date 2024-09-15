"""Blueprint Captures API."""

from __future__ import annotations


from fastapi import APIRouter, HTTPException, Request

from app.core.raspiconfig import RaspiConfigError, raspiconfig

router = APIRouter()


@router.post("/video/stop", status_code=204)
@router.post("/video/start", status_code=204)
async def camera(request: Request):
    """Get capture video."""
    try:
        if request.endpoint == "api.captures_video_start":
            raspiconfig.send("cam 1")
        if request.endpoint == "api.captures_video_stop":
            raspiconfig.send("cam 0")
    except RaspiConfigError as error:
        raise HTTPException(422, error)


@router.post("/image", status_code=204)
async def image():
    """Get capture image."""
    try:
        raspiconfig.send("im")
    except RaspiConfigError as error:
        raise HTTPException(422, error)


@router.post("/timelapse/stop", status_code=204)
@router.post("/timelapse/start", status_code=204)
async def timelapse(request: Request):
    """Get capture Timelapse."""
    try:
        if request.endpoint == "captures_timelapse_start":
            raspiconfig.send("tl 1")
        if request.endpoint == "captures_timelapse_stop":
            raspiconfig.send("tl 0")
    except RaspiConfigError as error:
        raise HTTPException(422, error)

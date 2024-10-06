"""Api system."""

import semver
from aiohttp import ClientError, ClientSession
from fastapi import APIRouter, HTTPException, Query
from sqlmodel import select

from app.api.depends import SessionDep
from app.core.config import Locale, Type, config
from app.core.process import execute_cmd, self_terminate
from app.core.raspiconfig import RaspiConfigError, raspiconfig
from app.core.utils import disk_usage
from app.exceptions import ViewPiCamException
from app.models import Command, FreeDisk, Presets, UserLevel

router = APIRouter()


@router.post("/restart", status_code=204)
async def post_restart():
    """Restart system."""
    try:
        execute_cmd("echo s > /proc/sysrq-trigger")
        execute_cmd("echo b > /proc/sysrq-trigger")
    except ViewPiCamException as error:
        raise HTTPException(422, error)


@router.post("/reset", status_code=204)
async def reset():
    """Reset application."""
    pass


@router.post("/shutdown", status_code=204)
async def post_halted():
    """Halt system."""
    try:
        execute_cmd("echo s > /proc/sysrq-trigger")
        execute_cmd("echo o > /proc/sysrq-trigger")
    except ViewPiCamException as error:
        raise HTTPException(422, error)


@router.post("/restart/app", status_code=204)
async def post_restart_app():
    """Restart application."""
    try:
        await self_terminate()
    except ViewPiCamException as error:
        raise HTTPException(422, error)


@router.post("/command", status_code=204)
async def post_command(command: Command):
    """Send command to control fifo."""
    if cmd := command.cmd:
        try:
            if params := command.params:
                params = " ".join(params)
                raspiconfig.send(f"{cmd} {params}")
            else:
                raspiconfig.send(f"{cmd}")
            return
        except RaspiConfigError as error:
            raise HTTPException(422, str(error))
    raise HTTPException(404, f"Command not found {cmd}")


@router.get("/version")
async def get_version():
    """Get version."""
    try:
        async with ClientSession() as session:
            async with session.get(config.GIT_URL) as response:
                response.raise_for_status()
                rjson = await response.json()

        rjson["app_version"] = rjson.get("tag_name").replace("v", "")
        current_version = config.VERSION.replace("v", "")
        rjson.update(
            {
                "current_version": current_version,
                "update_available": semver.compare(
                    rjson["app_version"], current_version
                ),
            }
        )
        return rjson
    except (ValueError, ClientError) as error:
        raise HTTPException(422, str(error))


@router.get("/disk/free")
async def get_freedisks() -> FreeDisk:
    """Get free space."""
    total, used, free, prc, color = disk_usage()
    return {
        "total": total,
        "used": used,
        "free": free,
        "prc": prc,
        "color": color,
    }


@router.get("/locales")
async def get_locales() -> list[Locale]:
    """Get all languages."""
    return config.LOCALES


@router.get("/presets")
async def get_presets(
    session: SessionDep, preset: Type | None = Query(description="Preset", default=None)
) -> list[Presets]:
    """Presets video."""
    if preset:
        return session.exec(select(Presets).filter_by(mode=preset)).all()
    return session.get_all(Presets)


@router.get("/userlevel")
async def get_userlevel() -> list[UserLevel]:
    """Get user level."""
    return [UserLevel(name=key, right=value) for key, value in config.USERLEVEL.items()]

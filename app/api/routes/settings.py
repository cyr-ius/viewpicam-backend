"""Blueprint Settings API."""

import logging
from datetime import datetime as dt

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlmodel import delete

from app.api.depends import SessionDep
from app.core.config import config
from app.core.filer import allowed_file, update_img_db, zip_extract, zip_folder
from app.core.raspiconfig import RaspiConfigError, raspiconfig
from app.core.settings import read, write
from app.models import Config, Files, Macro

router = APIRouter()
logger = logging.getLogger("uvicorn.error")


@router.get("/")
async def get() -> Config:
    """Get settings."""
    return read()


@router.post("/", status_code=204)
async def post(config: Config):
    """Set settings."""
    write(config.model_dump())

    if loglevel := config.loglevel:
        logger.setLevel(loglevel)
        logger.debug(f"Log level: {loglevel}")


@router.get("/macros")
async def get_macro() -> list[Macro]:
    """Get macros."""
    macros = []
    config = await _async_get_config()
    for key, value in config.items():
        if state := (value[:1] == "-"):
            value = value[1:]
        macros.append(Macro(name=key, command=value, state=not state))
    return macros


@router.post("/macros", status_code=204)
async def post_macro(macro: Macro):
    """Set macro."""
    if macro:
        config = await _async_get_config()
        for idx, name in enumerate(config.keys()):
            if macro.name == name:
                break

        cmd = macro.command
        if not macro.state:
            cmd = f"-{cmd}"
        try:
            raspiconfig.send(f"um {idx} {cmd}")
        except RaspiConfigError as error:
            raise HTTPException(422, error.args[0].strerror)


@router.get("/backup")
async def get_backup():
    date_str = dt.now().strftime("%Y%m%d_%H%M%S")
    zipname = f"config_{date_str}.zip"
    zip_file = zip_folder(config.CONFIG_FOLDER)

    headers = {"Content-Disposition": f"attachment; filename={zipname}"}
    return StreamingResponse(zip_file, media_type="application/zip", headers=headers)


@router.post("/restore", status_code=204)
async def post_restore(session: SessionDep, file: UploadFile):
    if file and allowed_file(file):
        zip_extract(file.file, config.CONFIG_FOLDER)
        session.exec(delete(Files))
        session.commit()
        update_img_db()


async def _async_get_config():
    """Return config."""
    return {item: getattr(raspiconfig, item) for item in config.MACROS}

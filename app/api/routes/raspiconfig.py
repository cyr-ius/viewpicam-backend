"""Api system."""

import os
import time

from fastapi import APIRouter, HTTPException, Query

from app.core.raspiconfig import RaspiConfigError, raspiconfig
from app.models import Command

router = APIRouter()


@router.get("/")
async def get(
    type: str = Query(
        description="All settings ou User settings [sys|user] (async default:sys)",
        default="sys",
    ),
):
    """Get config settings."""
    raspiconfig.refresh()
    if type == "user":
        return raspiconfig.user_config
    return raspiconfig.raspi_config


@router.post("/command", status_code=204)
async def post(command: Command):
    """Send command to control fifo."""
    if cmd := command.cmd:
        try:
            if params := command.params:
                params = [str(item) for item in params]
                params = " ".join(params)
                raspiconfig.send(f"{cmd} {params}")
            else:
                raspiconfig.send(f"{cmd}")
        except RaspiConfigError as error:
            raise HTTPException(422, str(error))
    raise HTTPException(404, f"Command not found {cmd}")


@router.get("/status")
async def get_status(last: str = Query(description="Last content", default=None)):
    """Get status."""
    file_content = ""
    if not os.path.isfile(raspiconfig.status_file):
        raise HTTPException(422, "Status file not found.")
    for _ in range(0, 30):
        with open(raspiconfig.status_file, encoding="utf-8") as file:
            file_content = file.read()
            if file_content != last:
                break
            time.sleep(0.1)
            file.close()
    os.popen(f"touch {raspiconfig.status_file}")
    return {"status": str(file_content)}

"""Api system."""

import asyncio
import logging
import os
import time

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect

from app.core.config import config
from app.core.raspiconfig import RaspiConfigError, raspiconfig
from app.models import Command

router = APIRouter()
logger = logging.getLogger("uvicorn.error")


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
    try:
        cmd = command.cmd
        if params := command.params:
            params = [str(item) for item in params]
            params = " ".join(params)
            raspiconfig.send(f"{cmd} {params}")
        else:
            raspiconfig.send(f"{cmd}")
    except RaspiConfigError as error:
        raise HTTPException(422, str(error))


@router.get("/status")
async def get_status(last: str = Query(description="Last content", default=None)):
    """Get status."""
    file_content = ""
    if not os.path.isfile(raspiconfig.status_file):
        raise HTTPException(422, "Status file not found.")
    for _ in range(0, config.RETRY_STATUS):
        with open(raspiconfig.status_file, encoding="utf-8") as file:
            file_content = file.read()
            if file_content != last:
                break
            time.sleep(config.SLEEP_STATUS)
            file.close()
    os.popen(f"touch {raspiconfig.status_file}")
    return {"status": str(file_content)}


@router.websocket("/status")
async def websocket_endpoint(websocket: WebSocket):
    """Websocket status"""
    await websocket.accept()
    try:
        while True:
            await asyncio.sleep(0.25)
            with open(raspiconfig.status_file, "r") as file:
                file_content = file.read()
            await websocket.send_json(file_content)

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")

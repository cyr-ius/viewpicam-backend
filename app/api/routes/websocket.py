"""Api system."""

import asyncio
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.raspiconfig import raspiconfig

router = APIRouter()

logger = logging.getLogger("uvicorn.error")


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

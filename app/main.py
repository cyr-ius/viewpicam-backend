"""ViewPI Camera."""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.routing import APIRoute

from app.api.main import api_router
from app.core.config import config
from app.core.log import set_log_level
from app.core.process import get_pid
from app.core.raspiconfig import raspiconfig
from app.core.settings import read
from app.core.utils import set_timezone
from app.daemon.backgroundtask import main_start

logger = logging.getLogger("uvicorn.error")


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


def set_initial_config():
    data = read()
    config.GMT_OFFSET = data["gmt_offset"]
    config.LOG_LEVEL = data["loglevel"]
    set_log_level(config.LOG_LEVEL)
    set_timezone(config.GMT_OFFSET)


app = FastAPI(
    title=config.SITE_NAME,
    debug=config.DEBUG,
    version=config.VERSION,
    description="Backend for RaspiMjpeg",
    generate_unique_id_function=custom_generate_unique_id,
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
)

# Start Raspiconfig
if config.SVC_RASPIMJPEG and not get_pid(config.RASPI_BINARY):
    raspiconfig.start()

# Start scheduler
if config.SVC_SCHEDULER:
    main_start()

# Load routes
app.include_router(api_router, prefix=config.API_V1_STR)

# Load initial configuration
set_initial_config()

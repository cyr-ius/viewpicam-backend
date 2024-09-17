"""Utils functions."""

import logging
import shutil

from app.core.log import write_log
from app.core.process import execute_cmd
from app.core.raspiconfig import raspiconfig

logger = logging.getLogger("uvicorn.error")


def disk_usage() -> tuple[int, int, int, int, str]:
    """Disk usage."""
    media_path = raspiconfig.media_path
    total, used, free = shutil.disk_usage(f"{media_path}")
    percent_used = round(used / total * 100)
    if percent_used > 98:
        colour = "Red"
    elif percent_used > 90:
        colour = "Orange"
    else:
        colour = "LightGreen"

    return (
        round(total / 1048576),
        round(used / 1048576),
        round(free / 1048576),
        int(percent_used),
        colour,
    )


def set_timezone(timezone: str) -> None:
    """Set localtime and timezone."""
    try:
        write_log(f"Set timezone {timezone}")
        execute_cmd(f"cp -f /usr/share/zoneinfo/{timezone} /etc/localtime")
    except Exception as error:
        logger.error(error)

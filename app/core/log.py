from __future__ import annotations

import json
import logging
import os
from datetime import datetime as dt
from json.decoder import JSONDecodeError

from app.core.raspiconfig import raspiconfig

logger = logging.getLogger("uvicorn.error")


def set_log_level(log_level: str) -> None:
    log_level = logging.getLevelName(log_level)
    logging.basicConfig(level=log_level)
    logger.setLevel(log_level)


def write_log(msg: str, level: str = "info") -> None:
    """Write log."""
    log_file = raspiconfig.log_file
    str_now = dt.now().strftime("%Y/%m/%d %H:%M:%S")
    getattr(logger, level)(msg)

    mode = "w" if not os.path.isfile(log_file) else "a"
    try:
        with open(log_file, mode=mode, encoding="utf-8") as file:
            line = json.dumps(
                {"datetime": str_now, "level": level.upper(), "msg": msg},
                separators=(",", ":"),
            )
            file.write(line + "\n")
    except FileNotFoundError as error:
        logger.error(error)


def delete_log(log_size: int) -> None:
    """Delete log."""
    log_file = raspiconfig.log_file
    if os.path.isfile(log_file):
        log_lines = open(log_file, encoding="utf-8").readlines()
        if len(log_lines) > log_size:
            with open(log_file, mode="w", encoding="utf-8") as file:
                file.writelines(log_lines[:log_size])
                file.close()


def get_logs(reverse: bool) -> list[str]:
    """Get log."""
    log_file = raspiconfig.log_file
    logs = []
    if os.path.isfile(log_file):
        with open(log_file, encoding="utf-8") as file:
            lines = file.readlines()
            file.close()

        for line in lines:
            line = line.replace("\n", "")
            try:
                line = json.loads(line)
            except JSONDecodeError:
                pass
            logs.append(line)

        logs.reverse()
    return logs

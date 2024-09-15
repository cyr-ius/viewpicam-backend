"""Rsync service."""

import logging
import os
from subprocess import PIPE, Popen

from app.core.config import config
from app.core.log import write_log
from app.core.process import get_pid
from app.core.raspiconfig import raspiconfig
from app.core.settings import read

logger = logging.getLogger("uvicorn.error")


class Rsync:
    def __init__(self) -> None:
        """Initialize."""

        self.media_path = raspiconfig.media_path
        self.binary = config.RSYNC_BINARY

        self.options = None
        self.pwd = None
        self.mode = None
        self.user = None
        self.host = None
        self.direction = None

    async def settings(self) -> None:
        """Get setting from database."""
        data = read()
        self.options = data.get("rs_options", [])
        self.pwd = data.get("rs_pwd")
        self.mode = data.get("rs_mode")
        self.user = data.get("rs_user")
        self.host = data.get("rs_remote_host")
        self.direction = data.get("rs_direction")

    async def execute(self) -> bool:
        """Rsync execute."""

        write_log("Rsync support started")

        await self.settings()

        if not isinstance(self.options, list):
            options = [self.options]

        options = " ".join(self.options)

        if self.mode == "SSH":
            ssh = "-e ssh"
            shee = "/"
        else:
            ssh = ""
            shee = ":"

        cmd = f"{self.binary} -v {options} --no-perms --exclude '*.th.jpg' {ssh} {self.media_path}/ {self.user}@{self.host}:{shee}{self.direction}"
        logger.info(cmd.strip())

        if not get_pid("/usr/bin/rsync"):
            process = Popen(
                cmd,
                shell=True,
                stdout=PIPE,
                stderr=PIPE,
                text="utf-8",
                env=dict(os.environ, RSYNC_PASSWORD=self.pwd),
            )

            for stdout_line in iter(process.stdout.readline, ""):
                logger.info(stdout_line.strip())
            process.stdout.close()

            for stderr_line in iter(process.stderr.readline, ""):
                self.write_log(stderr_line, "error")
            process.stderr.close()

            return_code = process.wait()
            if return_code > 0:
                self.write_log(f"Rsync failed ({return_code})", "error")
                return False

            self.write_log("Rsync successful")

        return True


class RsyncError(Exception):
    """Error for Rsync class."""


rsync = Rsync()

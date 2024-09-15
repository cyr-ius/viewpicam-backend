from __future__ import annotations

import fnmatch
from subprocess import PIPE, Popen

from psutil import ZombieProcess, process_iter

from app.exceptions import ViewPiCamException


def get_pid(pid_type: str | list[str]) -> int:
    """Return process id."""
    if not isinstance(pid_type, list):
        pid_type = [pid_type]

    for proc in process_iter():
        try:
            cmdline = proc.cmdline()
        except ZombieProcess:
            cmdline = []
        else:
            if all(fnmatch.filter(cmdline, item) for item in pid_type):
                return proc.pid
    return 0


def execute_cmd(cmd: str) -> None:
    """Execute shell command."""
    process = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
    output, error = process.communicate()
    if process.returncode != 0:
        err = error.decode("utf-8").replace("\n", "")
        raise ViewPiCamException(f"Error execute command ({err})")
    return output.decode("utf-8")

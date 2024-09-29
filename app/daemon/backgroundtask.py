"""Background task in another thread."""

from __future__ import annotations

import threading
from time import sleep

from fastapi import APIRouter

from app.core.log import write_log
from app.core.settings import read, write
from app.daemon.schedule import scheduler
from app.models import State

router = APIRouter()

running_threads = {}


class BackgroundTask(threading.Thread):
    def __init__(self, task_name):
        super().__init__()
        self.task_name = task_name
        self.is_stopped = False

    def run(self):
        scheduler()

    def stop(self):
        self.is_stopped = True


@router.post("/start", status_code=204)
async def start_task():
    main_start()


@router.post("/stop", status_code=204)
async def stop_task():
    main_stop()


@router.get("/status")
async def status() -> State:
    if "scheduler" in running_threads:
        if running_threads["scheduler"].is_alive():
            return {"start": 1, "stop": 0, "state": True}
        return {"start": 0, "stop": 1, "state": False}
    return {"start": 0, "stop": 0, "state": False}


def watchdog_task():
    write_log("Watchdog started")
    while True:
        sleep(0.25)
        settings = read()
        if settings.get("scheduler") == "start":
            if (
                "scheduler" in running_threads
                and not running_threads["scheduler"].is_alive()
            ):
                write_log("Watchdog has restarted the scheduler")
                running_threads["scheduler"].start()


def main_start():
    task = BackgroundTask("scheduler")
    running_threads["scheduler"] = task
    task.start()
    write({"scheduler": "start"})
    write_log("[MAIN] - Task scheduler started")


def main_stop():
    if "scheduler" in running_threads:
        running_threads["scheduler"].stop()
        del running_threads["scheduler"]
        write({"scheduler": "stop"})
        write_log("[MAIN] - Task scheduler stopped")

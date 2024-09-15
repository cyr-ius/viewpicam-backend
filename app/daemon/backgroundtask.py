"""Background task in another thread."""

from __future__ import annotations

import threading

from fastapi import APIRouter

from app.core.log import write_log
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
    task = BackgroundTask("scheduler")
    running_threads["scheduler"] = task
    task.start()
    write_log("Task scheduler started")


@router.post("/stop", status_code=204)
async def stop_task():
    if "scheduler" in running_threads:
        running_threads["scheduler"].stop()
        del running_threads["scheduler"]
        write_log("Task scheduler stopped")


@router.get("/status")
async def status() -> State:
    if "scheduler" in running_threads:
        if running_threads["scheduler"].is_stopped:
            return {"start": 0, "stop": 1, "state": False}
        return {"start": 1, "stop": 0, "state": True}
    return {"start": 0, "stop": 0, "state": False}


def main_start():
    task = BackgroundTask("scheduler")
    running_threads["scheduler"] = task
    task.start()
    write_log("[MAIN] - Task scheduler started")


def main_stop():
    if "scheduler" in running_threads:
        running_threads["scheduler"].stop()
        del running_threads["scheduler"]
        write_log("[MAIN] - Task scheduler stopped")

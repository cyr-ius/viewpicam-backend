"""Blueprint Camera."""

from __future__ import annotations

import glob
import os
import time

from fastapi import APIRouter, Response
from fastapi.responses import StreamingResponse

from app.core.raspiconfig import raspiconfig

router = APIRouter()


@router.get("/cam_pic")
def cam_pic(delay: int = 100):
    delay = float(delay / 1000)  # Unit (ms)
    cam_jpg = _get_shm_cam()
    time.sleep(delay)
    headers = {"Access-Control-Allow-Origin": "*", "Content-Type": "image/jpeg"}
    return Response(cam_jpg, headers=headers)


@router.get("/cam_picLatestTL")
def cam_pictl():
    media_path = raspiconfig.media_path
    list_of_files = filter(os.path.isfile, glob.glob(media_path + "*"))
    list_of_files = sorted(list_of_files, key=lambda x: os.stat(x).st_ctime)
    last_element = list_of_files[-1]
    last_jpeg = open(f"{media_path}/{last_element}", "rb").read()
    return Response(last_jpeg, headers={"Content-Type": "image/jpeg"})


# @router.get("/cam_get")
# def cam_get():
#     os.popen(f"touch {config.root_path}/status_mjpeg.txt")
#     cam_jpg = _get_shm_cam()
#     return Response(cam_jpg, headers={"Content-Type": "image/jpeg"})


@router.get("/cam_pic_new")
def cam_pic_new(delay: int = 100):
    delay = float(delay / 1000)  # Unit (ms)
    preview_path = raspiconfig.preview_path
    # return Response(
    #     _gather_img(preview_path, delay),
    #     mimetype="multipart/x-mixed-replace; boundary=PIderman",
    # )
    return StreamingResponse(
        _gather_img(preview_path, delay),
        media_type="multipart/x-mixed-replace; boundary=PIderman",
    )


def _get_shm_cam(preview_path=None):
    """Return binary data from cam.png."""
    preview_path = raspiconfig.preview_path if preview_path is None else preview_path

    display_path = (
        preview_path
        if os.path.isfile(preview_path)
        else "app/resources/unavailable.png"
    )

    with open(display_path, "rb") as file:
        return file.read()


def _gather_img(preview_path, delay=0.1):
    """Stream image."""
    while True:
        yield (
            b"--PIderman\r\nContent-Type: image/jpeg\r\n\r\n"
            + _get_shm_cam(preview_path)
            + b"\r\n"
        )
        time.sleep(delay)

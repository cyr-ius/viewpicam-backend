"""Files functions."""

from __future__ import annotations

import os
import re
import time
import zipfile
from datetime import datetime as dt
from io import BytesIO
from typing import Any

from sqlmodel import Session, select

from app.core.config import config
from app.core.db import engine
from app.core.log import write_log
from app.core.process import execute_cmd
from app.core.raspiconfig import raspiconfig
from app.exceptions import ViewPiCamException
from app.models import Files


def find_lapse_files(filename: str) -> list[str]:
    """Return lapse files."""
    media_path = raspiconfig.media_path
    files = {}
    lapsefiles = []

    batch = get_file_index(filename)
    padlen = len(batch)
    fullname = f"{media_path}/{data_file_name(filename)}"
    if not os.path.isfile(fullname):
        return lapsefiles
    start = os.path.getmtime(fullname)
    scanfiles = list_folder_files(f"{media_path}")
    for file in scanfiles:
        if file.find(batch):
            if (
                (not is_thumbnail(file))
                and (ext := get_file_ext(file))
                and ext == "jpg"
            ):
                f_date = os.path.getmtime(f"{media_path}/{file}")
                if f_date >= start:
                    files[file] = str(f_date) + file

    lapse_count = 1
    for key in sorted(files):
        if key[int(str(lapse_count).zfill(padlen)) :]:  # noqa: E203
            lapsefiles.append(f"{media_path}/{key}")
            lapse_count += 1
        else:
            break
    return lapsefiles


def delete_mediafiles(filename: str, delete: bool = True) -> int:
    """Delete all files associated with a thumb name."""
    media_path = raspiconfig.media_path
    size = 0
    type_file = get_file_type(filename)

    def compute_delete_file(file_name, size, delete):
        if os.path.isfile(file_name):
            size += get_file_size(file_name)
            if delete:
                os.remove(file_name)

    if type_file == "t":
        #  For time lapse try to delete all from this batch
        files = find_lapse_files(filename)
        for file in files:
            compute_delete_file(file, size, delete)
    else:
        thumb_file = data_file_name(filename)
        compute_delete_file(f"{media_path}/{thumb_file}", size, delete)

        if type_file == "v":
            raw_file = thumb_file[: thumb_file.find(".")]
            for file in (
                f"{media_path}/{thumb_file}.dat",
                f"{media_path}/{raw_file}.h264",
                f"{media_path}/{raw_file}.h264.bad",
                f"{media_path}/{raw_file}.h264.log",
            ):
                compute_delete_file(file, size, delete)

    compute_delete_file(f"{media_path}/{filename}", size, delete)

    # Remove database
    with Session(engine) as session:
        db_file = session.get(Files, get_file_id(filename))
        session.delete(db_file)
        session.commit()

    return round(size / 1024)


def data_file_name(file: str) -> str:
    """Return real filename."""
    subdir_char = raspiconfig.subdir_char
    i = file.rfind(".", 0, len(file) - 8)
    if i > 0:
        return file[:i].replace(subdir_char, "/")
    return ""


def data_file_ext(file: str) -> str:
    """Return real filename extension."""
    file = data_file_name(file)
    return get_file_ext(file)


def is_thumbnail(file: str) -> bool:
    """Return is thumbnail file."""
    return file[-7:] == config.THUMBNAIL_EXT


def is_existing(file: str) -> bool:
    media_path = raspiconfig.media_path
    return os.path.isfile(f"{media_path}/{file}")


def get_file_size(path) -> int:
    """Return file size."""
    return os.path.getsize(path)


def get_file_ext(file: str) -> str:
    """Return extension file."""
    _, ext = os.path.splitext(file)
    return ext[1:]


def get_file_type(file: str) -> str:
    """Return type file."""
    i = file.rfind(".", 0, len(file) - 8)
    if i > 0:
        return file[i + 1]
    return ""


def get_mp4_information(realname_path: str) -> list[str]:
    """Return MP4 information."""
    try:
        cmd = f"MP4Box -info '{realname_path}' 2>&1"
        response = execute_cmd(cmd)
        return response.replace("\t", "").split("\n")
    except ViewPiCamException:
        return list()


def get_file_duration(file: str) -> int:
    """Return duration mp4."""
    for item in get_mp4_information(file):
        duration = re.match("Duration (.*)", item)
        if duration:
            duration = dt.strptime(duration[1], "%H:%M:%S.%f")
            return duration.hour * 3600 + duration.minute * 60 + duration.second
    return 0


def get_file_index(file: str) -> str:
    """Return index file."""
    i = file.rfind(".", 0, len(file) - 8)
    if i > 0:
        return file[i + 2 : len(file) - 7]  # noqa: E203
    return ""


def get_file_timestamp(file: str) -> dt:
    """Return timestamp."""
    ext = (len(get_file_ext(file)) + 1) * -1
    sdatetime = file[:ext][-15:].replace("_", "")
    return dt.strptime(sdatetime, "%Y%m%d%H%M%S").timestamp()


def get_file_id(file: str) -> str:
    """Return id from file."""
    realname = data_file_name(file)
    return realname[:-4].replace("_", "")


def list_folder_files(path: str, exts: list[str] | None = None) -> list[str]:
    """List files in folder path."""
    if exts is None:
        exts = ["jpg", "mp4"]
    return [
        f
        for f in os.listdir(path)
        if os.path.isfile(os.path.join(path, f)) and (get_file_ext(f) in exts)
    ]


def get_file_info(file: str) -> dict[str, Any] | None:
    """Return information for file."""
    if not is_thumbnail(file):
        return

    media_path = raspiconfig.media_path
    type = get_file_type(file)
    realname = data_file_name(file)
    id = get_file_id(file)
    number = get_file_index(file)
    size = 0
    lapse_count = 0
    duration = 0
    realname_path = f"{media_path}/{realname}"
    with Session(engine) as session:
        locked = True if (thumb := session.get(Files, id)) and thumb.locked else False

    match type:
        case "v":
            icon = "bi-camera-reels"
        case "t":
            icon = "bi-images"
            lapse_count = len(find_lapse_files(file))
        case "i":
            icon = "bi-camera"
        case _:
            icon = "bi-camera"

    if os.path.isfile(realname_path):
        size = round(get_file_size(realname_path) / 1024)
        timestamp = get_file_timestamp(realname)
        if type == "v":
            duration = get_file_duration(realname_path)
    else:
        timestamp = (
            get_file_timestamp(realname) if realname != "" else get_file_timestamp(file)
        )

    return {
        "id": id,
        "name": file,
        "type": type,
        "size": size,
        "icon": icon,
        "datetime": dt.fromtimestamp(timestamp),
        "locked": locked,
        "realname": realname,
        "number": number,
        "lapse_count": lapse_count,
        "duration": duration,
    }


def get_sorted_files(folder: str, ascending: bool = True) -> list[str]:
    """Ordering files."""
    files = {}
    for file in list_folder_files(folder):
        if file != "." and file != ".." and is_thumbnail(file):
            files[file] = os.path.getmtime(f"{folder}/{file}")

    return sorted(files, reverse=ascending is False)


def maintain_folders(
    path, delete_main_files, delete_sub_files, root: bool = True
) -> bool:
    """Sanitize media folders."""
    empty = True
    for folder in list_folder_files(path):
        if os.path.isdir(folder):
            if not maintain_folders(folder, delete_main_files, delete_sub_files, False):
                empty = False
        else:
            if (delete_sub_files and not root) or (delete_main_files and root):
                os.remove(folder)
            else:
                empty = False
    return empty and not root and os.rmdir(path)


def zip_folder(path: str) -> BytesIO:
    """Zip folder."""
    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, "a") as zip_file:
        for root, dirs, files in os.walk(path):
            for file in files:
                try:
                    zip_file.write(os.path.join(root, file), file)
                except FileNotFoundError:
                    continue
    memory_file.seek(0)

    return memory_file


def zip_extract(file, path: str):
    """Extract zip file."""
    archive = zipfile.ZipFile(file)
    for file in archive.namelist():
        archive.extract(file, path)


def allowed_file(filename):
    type, sub_type = filename.content_type.split("/")
    return sub_type.lower() in config.ALLOWED_EXTENSIONS


def get_zip(files: list) -> BytesIO:
    """Zip files."""
    media_path = raspiconfig.media_path
    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, "a") as zip_file:
        for file in files:
            file_name = data_file_name(file)
            try:
                data = zipfile.ZipInfo(file_name)
                data.date_time = time.localtime(time.time())[:6]
                data.compress_type = zipfile.ZIP_DEFLATED
                zip_file.write(
                    f"{media_path}/{file_name}", file_name, data.compress_type
                )
            except FileNotFoundError:
                continue
    memory_file.seek(0)
    return memory_file


def update_img_db() -> None:
    """Add thumb to database."""
    media_path = raspiconfig.media_path
    with Session(engine) as session:
        files = session.exec(select(Files.id)).all()
        for thumb in list_folder_files(media_path):
            if (
                is_thumbnail(thumb)
                and (get_file_id(thumb) not in files)
                and is_existing(data_file_name(thumb))
            ):
                info = get_file_info(thumb)
                file = Files(**info)
                files.append(file.id)
                session.add(file)
                session.commit()
                write_log(f"Add {file.id} to database")

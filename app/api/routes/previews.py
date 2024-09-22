"""Api gallery."""

from datetime import datetime as dt

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.api.depends import SessionDep
from app.core.filer import delete_mediafiles, get_zip, maintain_folders
from app.core.raspiconfig import raspiconfig
from app.core.transform import get_thumbs, video_convert
from app.models import Files, LockMode

router = APIRouter()


@router.get("/")
async def get(
    order: str = Query(description="Ordering thumbnail [desc|asc]", default="desc"),
    show_types: str = Query(
        description="Show types [both|image|video]", default="both"
    ),
    time_filter: int = Query(description="Time filter", default=1),
) -> list[Files]:
    """Get all media files."""
    return get_thumbs(order.lower(), show_types.lower(), time_filter)


@router.delete("/")
async def delete(session: SessionDep, files: list[str]) -> list[str]:
    """Delete all files or files list"""
    deleted_ids = []
    if files:
        for id in files:
            if thumb := session.get_or_404(Files, id):
                if thumb.locked:
                    continue
                delete_mediafiles(thumb.name)
                maintain_folders(raspiconfig.media_path, False, False)
                deleted_ids.append(id)
    else:
        maintain_folders(raspiconfig.media_path, True, True)
    session.close()
    return deleted_ids


@router.get("/{id}")
async def get_thumb(session: SessionDep, id: str) -> Files:
    """Get file information."""
    return session.get_or_404(Files, id, error_desc="Thumb not found")


@router.delete("/{id}", status_code=204)
async def delete_thumb(session: SessionDep, id: str):
    """Delete file."""
    thumb = session.get_or_404(Files, id, error_desc="Thumb not found")
    if thumb.locked:
        raise HTTPException(422, f"Protected thumbnail ({id})")
    delete_mediafiles(thumb.name)
    maintain_folders(raspiconfig.media_path, False, False)


@router.post("/lock_mode", status_code=204)
async def post_thumb(session: SessionDep, lock_mode: LockMode):
    """Lock Mode."""
    ids = lock_mode["ids"]
    mode = lock_mode["mode"] is True
    ids = [ids] if isinstance(ids, str) else ids
    for id in ids:
        db_file = session.get_or_404(Files, id, error_desc="Thumb not found")
        db_file.sqlmodel_update({"locked": mode})
        session.add(db_file)
    session.commit()


@router.post("/{id}/lock", status_code=204)
async def post_lock(session: SessionDep, id: str):
    """Lock."""
    db_file = session.get_or_404(Files, id, error_desc="Thumb not found")
    if db_file.locked is True:
        return {"message": "Thumb is already locked"}, 201
    db_file.sqlmodel_update({"locked": True})
    session.add(db_file)
    session.commit()


@router.post("/{id}/unlock", status_code=204)
async def post_unlock(session: SessionDep, id: str):
    """Unlock."""
    db_file = session.get_or_404(Files, id, error_desc="Thumb not found")
    if db_file.locked is False:
        return {"message": "Thumb is already unlocked"}, 201
    db_file.sqlmodel_update({"locked": False})
    session.add(db_file)
    session.commit()


@router.post("/{id}/convert", status_code=204)
async def post_convert(session: SessionDep, id: str):
    """Coonvert timelapse."""
    thumb = session.get_or_404(Files, id, error_desc="Thumb not found")
    video_convert(thumb.name)


@router.post("/zipfile", response_class=StreamingResponse, responses={200: {"content": {"application/zip": {}} }})
async def post_zipfile(session: SessionDep, thumbs: list[str] | str):
    """Make Zip from thumbs list."""
    date_str = dt.now().strftime("%Y%m%d_%H%M%S")
    zipname = f"cam_{date_str}.zip"

    thumbs = [thumbs] if isinstance(thumbs, str) else thumbs
    if thumbs:
        zip_list = [
            thumb.name for id in thumbs if (thumb := session.get_or_404(Files, id))
        ]
        raw_file = get_zip(zip_list)

    headers = {"Content-Disposition": f"attachment; filename={zipname}"}
    return StreamingResponse(raw_file, media_type="application/zip", headers=headers)

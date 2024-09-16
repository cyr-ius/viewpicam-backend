"""Api logs."""

from datetime import datetime as dt

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from app.core.log import delete_log, get_logs
from app.core.raspiconfig import raspiconfig
from app.models import Log

router = APIRouter()


@router.get("/")
async def get(
    reverse: bool = Query(description="Ordering display (True|False)",default=True),
) -> list[Log]:
    """List log."""
    return get_logs(reverse)


@router.delete("/", status_code=204)
async def delete():
    """Delete log."""
    try:
        delete_log(1)
    except Exception as error:  # pylint: disable=W0718
        raise HTTPException(422, error)


@router.get("/download")
async def download():
    """Log."""
    date_str = dt.now().strftime("%Y%m%d_%H%M%S")
    logname = f"viewpicam_{date_str}.log"

    response = FileResponse(
        path=raspiconfig.log_file,
        content_disposition_type="attachment",
        filename=logname,
    )
    return response

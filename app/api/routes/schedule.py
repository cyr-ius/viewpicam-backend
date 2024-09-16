"""Api scheduler."""

from datetime import datetime as dt
from datetime import timedelta as td
from datetime import timezone

import pytz
import zoneinfo
from fastapi import APIRouter, HTTPException
from sqlmodel import select
from suntime import Sun

from app.api.depends import SessionDep
from app.core.config import config
from app.core.fifo import send_pipe
from app.core.log import set_log_level, write_log
from app.core.settings import read, write
from app.core.utils import set_timezone
from app.exceptions import ViewPiCamException
from app.models import (
    Calendar,
    Date_Time,
    Period,
    Schedule,
    Scheduler,
    SchedulerUpdate,
    SchedulerWithCalendars,
    Settings,
)

router = APIRouter()


@router.get("/")
async def get() -> Schedule:
    """Get settings scheduler."""
    return read()


@router.put("/", status_code=204)
async def put(schedule: Schedule):
    """Set settings."""
    data = read()
    cur_tz = data["gmt_offset"]
    write(schedule.model_dump())

    if (new_tz := data["gmt_offset"]) != cur_tz:
        try:
            set_timezone(new_tz)
        except ViewPiCamException as error:
            write_log(f"[Timezone] {str(error)}", "error")

    set_log_level(data["loglevel"])

    send_pipe(config.SCHEDULE_RESET)


@router.put("/scheduler", status_code=204)
async def put_scheduler(session: SessionDep, scheduler: list[SchedulerUpdate]):
    """Set settings."""
    for item in scheduler:
        schedule = session.exec(
            select(Scheduler).filter_by(daysmode_id=item.daysmode.id, id=int(item.id))
        ).first()
        schedule.command_on = item.command_on
        schedule.command_off = item.command_off
        schedule.mode = item.mode
        schedule.calendars = []
        for key, value in item.calendars.items():
            if value:
                cal = session.exec(
                    select(Calendar).filter_by(name=key.capitalize())
                ).first()
                schedule.calendars.append(cal)
        session.commit()

    send_pipe(config.SCHEDULE_RESET)


@router.get("/period/{id}", status_code=201)
async def get_period(session: SessionDep, id: int | None = None) -> Period:
    """Post day mode and return period."""
    if id not in [0, 1, 2]:
        raise HTTPException(422, "Daymode not exist")
    return {"period": get_calendar(session, id)}


@router.get("/sun/sunrise", status_code=201)
async def get_sunrise(session: SessionDep) -> Date_Time:
    """Get sunrise datetime."""
    return {"datetime": sun_info(session, "sunrise")}


@router.get("/sun/sunset", status_code=201)
async def get_sunset(session: SessionDep) -> Date_Time:
    """Get sunset datetime."""
    return {"datetime": sun_info(session, "sunset")}


@router.get("/gmtoffset", status_code=201)
async def get_gmtoffset(session: SessionDep):
    """GMT Offset."""
    data = read()
    return {"gmt_offset": data["gmt_offset"]}


@router.get("/timezones", status_code=201)
async def get_timezone() -> list[str]:
    """Timezone."""
    timezones = zoneinfo.available_timezones()
    return list(timezones)


@router.get("/scheduler")
@router.get("/scheduler/{daymode_id}")
async def get_scheduler(
    session: SessionDep, daymode_id: int | None = None
) -> list[SchedulerWithCalendars]:
    """Get settings scheduler."""
    if daymode_id is not None:
        return session.exec(select(Scheduler).filter_by(daysmode_id=daymode_id)).all()
    return session.get_all(Scheduler)


def time_offset(offset: int | float | str = 0) -> td:
    """Get time offset."""
    if isinstance(offset, (int, float)):
        noffset = td(hours=offset)
    else:
        try:
            gmt_time = dt.now(pytz.timezone(offset))
            noffset = gmt_time.utcoffset()
        except pytz.UnknownTimeZoneError:
            noffset = td(hours=0)
    return noffset


def utc_offset(offset) -> timezone:
    return timezone(td(seconds=offset))


def dt_now() -> dt:
    """Get current local time."""
    now = dt.utcnow()
    gmt_offset = config.GMT_OFFSET

    if gmt_offset:
        offset = time_offset(gmt_offset)
        now = (now + offset).replace(tzinfo=utc_offset(offset.seconds))
    return now


def sun_info(session: SessionDep, mode: str) -> dt:
    """Return sunset or sunrise datetime."""
    data = read()
    offset = time_offset(data["gmt_offset"])
    sun = Sun(data["latitude"], data["longitude"])
    if mode.lower() == "sunset":
        sun_time = sun.get_sunset_time()
    else:
        sun_time = sun.get_sunrise_time()
    return sun_time.replace(tzinfo=utc_offset(offset.seconds)) + offset


def get_calendar(session: SessionDep, daymode: int) -> int:
    """Get calendar."""
    now = dt_now()
    sunrise = sun_info(session, "sunrise")
    sunset = sun_info(session, "sunset")
    data = read()

    match daymode:
        case 0:
            if now < (sunrise + td(minutes=data["dawnstart_minutes"])):
                # Night
                mem_sch = session.exec(
                    select(Scheduler).filter_by(period="night", daysmode_id=daymode)
                ).first()
            elif now < (sunrise + td(minutes=data["daystart_minutes"])):
                # Dawn
                mem_sch = session.exec(
                    select(Scheduler).filter_by(period="dawn", daysmode_id=daymode)
                ).first()
            elif now > (sunset + td(minutes=data["duskend_minutes"])):
                # Night
                mem_sch = session.exec(
                    select(Scheduler).filter_by(period="night", daysmode_id=daymode)
                ).first()

            elif now > (sunset + td(minutes=data["dayend_minutes"])):
                # Dusk
                mem_sch = session.exec(
                    select(Scheduler).filter_by(period="dusk", daysmode_id=daymode)
                ).first()

            else:
                # Day
                mem_sch = session.exec(
                    select(Scheduler).filter_by(period="day", daysmode_id=daymode)
                ).first()

        case 1:
            # AllDay
            mem_sch = session.exec(
                select(Scheduler).filter_by(period="allday", daysmode_id=daymode)
            ).first()
        case 2:
            # Times
            schedulers = session.exec(select(Scheduler).filter_by(daysmode_id=2)).all()
            max_less_v = -1
            for scheduler in schedulers:
                str_time = scheduler.period
                f_mins = dt.strptime(str_time, "%H:%M")
                if (
                    f_mins.time() < now.time()
                    and (f_mins.hour * 60 + f_mins.minute) > max_less_v
                ):
                    max_less_v = f_mins.hour * 60 + f_mins.minute
                    mem_sch = scheduler

    return mem_sch.period

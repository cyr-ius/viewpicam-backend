"""Schema database."""

import uuid
from datetime import datetime as dt

import qrcode
import qrcode.image.svg
from pydantic import BaseModel, field_serializer
from sqlmodel import JSON, Column, Field, Relationship, SQLModel

from app.core.config import Level, Locale, Type


class Settings(SQLModel, table=True):
    __tablename__ = "settings"
    id: int | None = Field(default=None, primary_key=True)
    data: dict = Field(default_factory=dict, sa_column=Column(JSON))

    class Config:
        arbitrary_types_allowed = True


# -- Ubutons --


class ButtonBase(SQLModel):
    name: str = Field(description="Button name")
    macro: str = Field(description="Script name")
    style: str | None = Field(description="Class", default=None)
    other: str | None = Field(description="Style", default=None)
    css_class: str | None = Field(description="Others options", default=None)
    display: bool = Field(default=False, description="Display button")


class Buttons(ButtonBase, table=True):
    __tablename__ = "ubuttons"
    id: int | None = Field(default=None, primary_key=True)


class ButtonCreate(ButtonBase):
    pass


class ButtonPublic(ButtonBase):
    id: int


class ButtonUpdate(SQLModel):
    name: str | None = Field(description="Button name")
    macro: str | None = Field(description="Script name")
    style: str | None = Field(description="Class", default=None)
    other: str | None = Field(description="Style", default=None)
    css_class: str | None = Field(description="Others options", default=None)
    display: bool | None = Field(default=False, description="Display button")


# -- Files --


class FileBase(SQLModel):
    name: str = Field(index=True, unique=True, description="File name")
    type: str = Field(description="I/T/V")
    size: int = Field(description="Size")
    icon: str = Field(description="Icon")
    datetime: dt = Field(description="DateTime")
    locked: bool = Field(description="Read/Write right on disk", default=False)
    realname: str = Field(index=True, unique=True)
    number: str = Field(description="Index")
    lapse_count: int | None = Field(description="image numbers of timelapse")
    duration: int | None = Field(description="image numbers of timelapse")


class Files(FileBase, table=True):
    __tablename__ = "files"
    id: str | None = Field(default=None, primary_key=True)


class FileCreate(FileBase):
    pass


class FilePublic(FileBase):
    id: str


class FileUpdate(SQLModel):
    name: str | None = Field(index=True, unique=True, description="File name")
    type: str | None = Field(description="I/T/V")
    size: int | None = Field(description="Size")
    icon: str | None = Field(description="Icon")
    datetime: dt | None = Field(description="DateTime")
    locked: bool | None = Field(description="Read/Write right on disk", default=False)
    realname: str | None = Field(index=True, unique=True)
    number: str | None = Field(description="Index")
    lapse_count: int | None = Field(description="image numbers of timelapse")
    duration: int | None = Field(description="image numbers of timelapse")


# -- Multiview --


class MultiviewsBase(SQLModel):
    delay: int = Field(description="Delay")
    state: int = Field(description="State visible")
    url: str = Field(description="Url")


class Multiviews(MultiviewsBase, table=True):
    __tablename__ = "multiviews"
    id: int | None = Field(default=None, primary_key=True)


class MultiviewCreate(MultiviewsBase):
    pass


class MultiviewPublic(MultiviewsBase):
    id: int


class MultiviewUpdate(SQLModel):
    delay: int | None = Field(description="Delay")
    state: int | None = Field(description="State visible")
    url: str | None = Field(description="Url")


# -- Users --


class UserBase(SQLModel):
    enabled: bool = Field(default=True)
    locale: str = Field(default="en")
    name: str = Field(unique=True)
    otp_confirmed: bool = Field(default=False)
    right: int = Field(foreign_key="roles.level")


class User(UserBase, table=True):
    __tablename__ = "users"
    id: int | None = Field(default=None, primary_key=True)
    alternative_id: int = Field(default=str(uuid.uuid4()))
    secret: str | None
    otp_secret: str | None = None
    api_token: str | None = None
    cam_token: str | None = None

    roles: "Roles" = Relationship(back_populates="users")


class UserCreate(UserBase):
    password: str


class UserPublic(UserBase):
    id: int


class UserUpdate(SQLModel):
    enabled: bool | None = None
    locale: str | None = None
    name: str | None = None
    password: str | None = None
    otp_confirmed: bool | None = None
    right: int | None = Field(foreign_key="roles.level", default=None)


# -- Tables --


class Roles(SQLModel, table=True):
    __tablename__ = "roles"
    level: int = Field(primary_key=True)
    name: str = Field(unique=True)
    users: "User" = Relationship(back_populates="roles")


class Presets(SQLModel, table=True):
    __tablename__ = "presets"
    id: int | None = Field(default=None, primary_key=True)
    mode: str
    name: str
    width: int
    height: int
    fps: int
    i_width: int
    i_height: int
    i_rate: int


class Calendar(SQLModel, table=True):
    __tablename__ = "calendar"
    id: int | None = Field(default=None, primary_key=True)
    name: str


class DaysMode(SQLModel, table=True):
    __tablename__ = "daysmode"
    id: int | None = Field(default=None, primary_key=True)
    name: str

    scheduler: "Scheduler" = Relationship(back_populates="daysmode")


#  -- Relation Any to Any --


class Scheduler_Calendar(SQLModel, table=True):
    scheduler_id: int | None = Field(
        default=None, foreign_key="scheduler.id", nullable=False, primary_key=True
    )
    calendar_id: int | None = Field(
        default=None, foreign_key="calendar.id", nullable=False, primary_key=True
    )


# -- Scheduler --
class SchedulerBase(SQLModel):
    command_on: str
    command_off: str
    mode: str
    enabled: bool
    period: str
    daysmode_id: int = Field(foreign_key="daysmode.id")


class Scheduler(SchedulerBase, table=True):
    __tablename__ = "scheduler"
    id: int | None = Field(default=None, primary_key=True)

    daysmode: "DaysMode" = Relationship(back_populates="scheduler")
    calendars: list["Calendar"] = Relationship(link_model=Scheduler_Calendar)


class SchedulerCreate(SchedulerBase):
    pass


class SchedulerPublic(SchedulerBase):
    id: int


class SchedulerUpdate(SQLModel):
    id: int
    command_on: str | None = None
    command_off: str | None = None
    mode: str | None = None
    enabled: bool | None = None
    period: str | None = None
    daysmode_id: int | None = None
    daysmode: "DaysMode"
    calendars: dict[str, int | bool]


class Week(BaseModel):
    Mon: int
    Tue: int
    Wed: int
    Thu: int
    Fri: int
    Sat: int
    Sun: int


class SchedulerWithCalendars(SchedulerPublic):
    calendars: list[Calendar]
    daysmode: DaysMode

    @field_serializer("calendars")
    def serialize_calendars(self, obj: list[Calendar], _info) -> Week:
        calendar = {}
        for idx, day in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
            for item in obj:
                if item.name == day:
                    calendar.update({day: 1})
                    break
            else:
                calendar.update({day: 0})

        return Week.model_validate(calendar)


# -- Pydantics Model native --


class ApiToken(BaseModel):
    api_token: str | None = None


class CameraToken(BaseModel):
    cam_token: str | None = None


class Config(BaseModel):
    servo: bool = Field(description="Servo", default=False)
    pipan: bool = Field(description="Pipan", default=False)
    pilight: bool = Field(description="Pi Light", default=False)
    upreset: Type = Field(default="v2", description="Class")
    loglevel: Level = Field(default="INFO", description="Log level")

    class Config:
        use_enum_values = True


class Date_Time(BaseModel):
    datetime: dt


class FreeDisk(BaseModel):
    total: int
    used: int
    free: int
    prc: int
    color: str


class State(BaseModel):
    start: int
    stop: int
    state: bool


class TokenPayload(BaseModel):
    id: int
    sub: str


class TokenInfo(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int


class Locales(BaseModel):
    locales: Locale


class Log(BaseModel):
    datetime: str
    level: Level
    msg: str

    class Config:
        use_enum_values = True


class Login(BaseModel):
    username: str
    password: str
    otp_code: str | None = None


class Macro(BaseModel):
    name: str = Field(description="Macro name")
    command: str = Field(description="Script execute")
    state: bool = Field(description="Enable", default=False)


class Otp(BaseModel):
    id: int = Field(description="Id")
    name: str = Field(description="The user name")
    otp_confirmed: bool = Field(description="otp status", default=False)
    otp_secret: str | None = Field(
        description="QR Code picture", default=None, alias="otp_svg"
    )

    @field_serializer("otp_secret")
    def serializer_otp_svg(self, obj, _info) -> str:
        """Display QR Code."""
        if not obj:
            return
        uri = f"otpauth://totp/viewpicam:{self.name}?secret={obj}&issuer=viewpicam"
        qr = qrcode.QRCode(image_factory=qrcode.image.svg.SvgPathImage)
        qr.make(fit=True)
        qr.add_data(uri)
        img = qr.make_image()
        return img.to_string(encoding="unicode")


class Period(BaseModel):
    period: str = Field(description="Period")


class Register(Login):
    password_2: str


class LockMode(BaseModel):
    mode: bool = Field(description="Locked is true")
    ids: list[str]


class Command(BaseModel):
    cmd: str = Field(description="Command")
    params: list[str | int] | None = Field(description="Parameters", default=None)


class Rsync(BaseModel):
    rs_enabled: bool = Field(default=False)
    rs_user: str | None = Field(default=None)
    rs_pwd: str | None = Field(default=None)
    rs_direction: str | None = Field(default=None)
    rs_mode: str = Field(default="Module")
    rs_remote_host: str | None = Field(default=None)
    rs_options: list[str] = Field(default=["-a", "-z"])


class Schedule(BaseModel):
    autocamera_interval: int
    autocapture_interval: int
    cmd_poll: float
    dawnstart_minutes: int
    dayend_minutes: int
    daymode: int
    daystart_minutes: int
    duskend_minutes: int
    gmt_offset: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    management_command: str | None = None
    management_interval: int
    max_capture: int
    mode_poll: int
    purgeimage_hours: int
    purgelapse_hours: int
    purgevideo_hours: int
    purgespace_level: int
    purgespace_modeex: int


class Secret(BaseModel):
    secret: str = Field(description="OTP code")

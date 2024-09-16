from __future__ import annotations

from enum import Enum

from pydantic_settings import BaseSettings, SettingsConfigDict


class Type(str, Enum):
    v2 = "v2"
    nimx219 = "N-IMX219"
    pimx219 = "P-IMX219"
    nov5647 = "N-OV5647"
    pov5647 = "P-OV5647"


class Level(str, Enum):
    info = "INFO"
    warning = "WARNING"
    error = "ERROR"
    debug = "DEBUG"


class Locale(str, Enum):
    fr = "FR"
    en = "EN"


class Right(int, Enum):
    min = 1
    standard = 2
    medium = 4
    max = 8


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="VIEWPICAM_",
        env_file=(".env", ".secret_key"),
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )

    API_V1_STR: str = "/api/v1"

    # GENERAL SETTINGS
    SITE_NAME: str = "ViewPI Camera"
    VERSION: str = "0.0.0"

    # BASIC APP CONFIG
    DEBUG: bool = False
    SECRET_KEY: str = "12345678900987654321"
    TOKEN_LIFETIME: int = 60  # minutes
    GMT_OFFSET: str = "Etc/UTC"

    # Allowed extension for mask file
    ALLOWED_EXTENSIONS: list[str] = ["pgm", "zip"]
    MASK_FILENAME: str = "motionmask.pgm"

    # Url and timeout to fetch version from github
    GIT_URL: str = "https://api.github.com/repos/cyr-ius/viewpi-cam/releases/latest"
    TIMEOUT: int = 10

    # File where default settings
    CONFIG_FOLDER: str = "./config"
    RASPI_CONFIG: str = "/etc/raspimjpeg"
    RASPI_BINARY: str = "/usr/bin/raspimjpeg"
    RSYNC_BINARY: str = "/usr/bin/rsync"

    SQLALCHEMY_DATABASE_URI: str = f"sqlite:///{CONFIG_FOLDER}/config.db"

    # Userlevel
    USERLEVEL_MIN: int = 1
    USERLEVEL_MINP: int = 2
    USERLEVEL_MEDIUM: int = 4
    USERLEVEL_MAX: int = 8
    USERLEVEL: dict[str, int] = {
        "min": USERLEVEL_MIN,
        "preview": USERLEVEL_MINP,
        "medium": USERLEVEL_MEDIUM,
        "max": USERLEVEL_MAX,
    }

    # Locales
    LOCALES: list[str] = ["EN", "FR"]
    LOG_LEVEL: str = "DEBUG"

    # Macros name files
    MACROS: list[str] = [
        "error_soft",
        "error_hard",
        "start_img",
        "end_img",
        "start_vid",
        "end_vid",
        "end_box",
        "do_cmd",
        "motion_event",
        "startstop",
    ]

    # Filter number
    TIME_FILTER_MAX: int = 8

    # Starts services
    SVC_RASPIMJPEG: bool = True
    SVC_SCHEDULER: bool = True

    # Schedule state
    SCHEDULE_RESET: int = 9
    SCHEDULE_UPDATE_VID: int = 8
    SCHEDULE_UPDATE_IMG: int = 7
    SCHEDULE_START: int = 1
    SCHEDULE_STOP: int = 0

    # Motion
    MOTION_URL: str = "http://127.0.0.1:6642/0/"
    MOTION_CONFIGBACKUP: str = "motionPars.json"
    MOTION_PARS: str = "motionPars"
    MOLTION_FILTER: list[str] = [
        "switchfilter",
        "threshold",
        "threshold_tune",
        "noise_level",
        "noise_tune",
        "despeckle",
        "despeckle_filter",
        "area_detect",
        "mask_file",
        "smart_mask_speed",
        "lightswitch",
        "minimum_motion_frames",
        "framerate",
        "minimum_frame_time",
        "netcam_url",
        "netcam_userpass",
        "gap",
        "event_gap",
        "on_event_start",
        "on_event_end",
        "on_motion_detected",
        "on_area_detected",
    ]


config = Config()

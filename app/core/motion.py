"""Motion functions."""

import configparser

from httpx import AsyncClient, HTTPError

from app.core.config import config
from app.core.process import get_pid


def is_motion():
    return get_pid("*/motion") != 0


async def async_get_motion() -> configparser.ConfigParser:
    """Get motion parameters."""
    rsp_txt = await async_get(f"{config.MOTION_URL}/config/list")
    return await async_parse_ini(rsp_txt)


async def async_set_motion(key: str, value: str | bool | int | float) -> None:
    """set motion parameter."""
    await async_get(f"{config.MOTION_URL}/config/set?{key}={value}")


async def async_write_motion() -> None:
    """set motion parameter."""
    await async_get(f"{config.MOTION_URL}/config/write")


async def async_pause_motion() -> None:
    """set motion parameter."""
    await async_get(f"{config.MOTION_URL}/config/pause")


async def async_start_motion() -> None:
    """set motion parameter."""
    await async_get(f"{config.MOTION_URL}/config/start")


async def async_restart_motion() -> configparser.ConfigParser:
    """set motion parameter."""
    await async_get(f"{config.MOTION_URL}/config/restart")
    rsp_text = await async_get(f"{config.MOTION_URL}/config/list")
    return await async_parse_ini(rsp_text)


async def async_get(url: str) -> str:
    """Get request."""
    try:
        async with AsyncClient() as client:
            response = await client.get(url)
    except (ValueError, HTTPError) as error:
        raise MotionError(error) from error
    return response.text()


async def async_parse_ini(raw_config: str) -> configparser.ConfigParser:
    """Parse motion file."""
    config = configparser.ConfigParser()
    config.read_string(raw_config)
    return config


class MotionError(Exception):
    """Error for Motion config."""

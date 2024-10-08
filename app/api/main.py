from fastapi import APIRouter, Security

from app.api.depends import get_camera_token, get_current_user
from app.api.routes import (
    authorize,
    buttons,
    camera,
    logs,
    motion,
    multiview,
    previews,
    raspiconfig,
    rsync,
    schedule,
    settings,
    system,
    totp,
    users,
    websocket,
)
from app.daemon import backgroundtask

api_router = APIRouter()
api_router.include_router(authorize.router, prefix="/idp", tags=["idp"])
api_router.include_router(
    buttons.router,
    prefix="/buttons",
    tags=["buttons"],
    dependencies=[Security(get_current_user)],
)
api_router.include_router(
    camera.router,
    prefix="/cam",
    tags=["camera"],
    dependencies=[Security(get_camera_token)],
)
api_router.include_router(
    logs.router,
    prefix="/logs",
    tags=["logs"],
    dependencies=[Security(get_current_user)],
)
api_router.include_router(
    motion.router,
    prefix="/motion",
    tags=["motion"],
    dependencies=[Security(get_current_user)],
)
api_router.include_router(
    multiview.router,
    prefix="/multiview",
    tags=["multiview"],
    dependencies=[Security(get_current_user)],
)
api_router.include_router(
    previews.router,
    prefix="/previews",
    tags=["previews"],
    dependencies=[Security(get_current_user)],
)
api_router.include_router(
    raspiconfig.router,
    prefix="/raspiconfig",
    tags=["raspiconfig"],
    dependencies=[Security(get_current_user)],
)
api_router.include_router(
    rsync.router,
    prefix="/rsync",
    tags=["rsync"],
    dependencies=[Security(get_current_user)],
)
api_router.include_router(
    schedule.router,
    prefix="/schedule",
    tags=["schedule"],
    dependencies=[Security(get_current_user)],
)
api_router.include_router(
    settings.router,
    prefix="/settings",
    tags=["settings"],
    dependencies=[Security(get_current_user)],
)
api_router.include_router(
    system.router,
    prefix="/system",
    tags=["system"],
    dependencies=[Security(get_current_user)],
)
api_router.include_router(
    totp.router, prefix="/otp", tags=["otp"], dependencies=[Security(get_current_user)]
)
api_router.include_router(
    users.router,
    prefix="/users",
    tags=["users"],
    dependencies=[Security(get_current_user)],
)
api_router.include_router(
    backgroundtask.router,
    prefix="/tasks",
    tags=["tasks"],
    dependencies=[Security(get_current_user)],
)
api_router.include_router(websocket.router, prefix="/ws", tags=["websocket"])

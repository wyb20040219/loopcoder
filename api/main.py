import logging

from fastapi import FastAPI

from fastapi.middleware.cors import (
    CORSMiddleware
)

from api.handlers import (
    register_exception_handlers
)

from api.lifespan import (
    lifespan
)

from api.middleware import (
    register_http_middleware
)

from api.routers.control import (
    router as control_router
)

from api.routers.dashboard import (
    router as dashboard_router
)

from api.routers.runs import (
    router as runs_router
)

from api.routers.system import (
    router as system_router
)

from api.settings import (
    get_api_settings
)


# ==========================================
# Settings
# ==========================================

settings = (
    get_api_settings()
)


# ==========================================
# Logging
# ==========================================

logging.basicConfig(
    level=getattr(
        logging,
        settings.log_level.upper(),
        logging.INFO
    ),
    format=(
        "%(asctime)s "
        "%(levelname)s "
        "%(name)s "
        "%(message)s"
    )
)


# ==========================================
# FastAPI App
# ==========================================

app = FastAPI(
    title=settings.app_name,
    description=(
        "LoopCoder长程Coding Agent的"
        "Control Plane接口。"
    ),
    version=settings.app_version,
    lifespan=lifespan
)


# ==========================================
# CORS Middleware
# ==========================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=(
        settings.cors_origin_list
    ),

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"]
)


# ==========================================
# HTTP Middleware
# ==========================================

register_http_middleware(
    app
)


# ==========================================
# Exception Handler
# ==========================================

register_exception_handlers(
    app
)


# ==========================================
# Routers
# ==========================================

app.include_router(
    system_router
)

app.include_router(
    control_router
)

app.include_router(
    runs_router
)

app.include_router(
    dashboard_router
)
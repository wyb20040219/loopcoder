import logging

from fastapi import FastAPI

from api.routers.system import (
    router as system_router
)

from api.routers.control import (
    router as control_router
)

from api.routers.runs import (
    router as runs_router
)

from api.routers.dashboard import (
    router as dashboard_router
)

from api.handlers import (
    register_exception_handlers
)

from api.middleware import (
    register_http_middleware
)


# ==========================================
# 基础日志配置
# ==========================================

logging.basicConfig(
    level=logging.INFO,
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
    title="LoopCoder Control Plane API",
    description=(
        "LoopCoder长程Coding Agent的"
        "只读Control Plane接口。"
        "\n\n"
        "用于查看Goal、Todo、Quota、"
        "Evidence、Attention和Run History。"
    ),
    version="0.1.0"
)


# ==========================================
# Middleware
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
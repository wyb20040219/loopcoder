
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


# ==========================================
# 创建 FastAPI 应用
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
# 注册统一异常处理器
# ==========================================

register_exception_handlers(app)


# ==========================================
# 注册 API Router
# ==========================================

app.include_router(system_router)

app.include_router(control_router)

app.include_router(runs_router)

app.include_router(dashboard_router)

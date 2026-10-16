import asyncio

from fastapi import (
    APIRouter
)

from api.errors import (
    ServiceUnavailableError
)

from api.schemas import (
    HealthResponse,
    ReadinessResponse
)

from control_store import (
    get_overview
)


router = APIRouter(
    tags=[
        "System"
    ]
)


# ==========================================
# Liveness
# ==========================================

@router.get(
    "/health",
    response_model=HealthResponse
)
async def health():

    return {
        "status":
            "ok",

        "service":
            "loopcoder-control-plane"
    }


# ==========================================
# Readiness
# ==========================================

@router.get(
    "/health/ready",
    response_model=ReadinessResponse
)
async def readiness():

    try:

        # ==================================
        # get_overview 是同步函数。
        #
        # 它最终涉及文件系统读取，
        # 所以不要直接阻塞 Event Loop。
        #
        # 将同步函数交给工作线程执行。
        # ==================================

        await asyncio.to_thread(
            get_overview
        )


    except Exception as exc:

        raise ServiceUnavailableError(
            detail=(
                "Control Plane数据"
                "暂时无法读取"
            )
        ) from exc


    return {
        "status":
            "ready",

        "service":
            "loopcoder-control-plane",

        "control_plane_readable":
            True
    }
import asyncio

from typing import Annotated

from fastapi import (
    APIRouter,
    Depends
)

from sqlalchemy import (
    text
)

from sqlalchemy.exc import (
    SQLAlchemyError
)

from sqlalchemy.orm import (
    Session
)

from api.errors import (
    ServiceUnavailableError
)

from api.schemas import (
    DatabaseHealthResponse,
    HealthResponse,
    ReadinessResponse
)

from control_store import (
    get_overview
)

from db.session import (
    get_db
)


router = APIRouter(
    tags=["System"]
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
        "status": "ok",
        "service":
            "loopcoder-control-plane"
    }


# ==========================================
# Control Plane Readiness
# ==========================================

@router.get(
    "/health/ready",
    response_model=ReadinessResponse
)
async def readiness():

    try:

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
        "status": "ready",
        "service":
            "loopcoder-control-plane",
        "control_plane_readable":
            True
    }


# ==========================================
# Database Health
# ==========================================

@router.get(
    "/health/db",
    response_model=(
        DatabaseHealthResponse
    )
)
def database_health(
    db: Annotated[
        Session,
        Depends(get_db)
    ]
):

    try:

        result = db.execute(
            text("SELECT 1")
        )

        value = (
            result.scalar_one()
        )

    except SQLAlchemyError as exc:

        raise ServiceUnavailableError(
            detail=(
                "MySQL数据库"
                "暂时无法访问"
            )
        ) from exc


    return {
        "status": "ready",
        "database": "mysql",
        "check": value == 1
    }
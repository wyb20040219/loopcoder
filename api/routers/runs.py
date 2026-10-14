
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Query
)

from api.schemas import (
    RunDetailResponse,
    RunSearchRequest,
    RunsResponse
)

from api.dependencies import (
    RunSearchCallable,
    get_run_search_service
)

from api.errors import (
    RunNotFoundError
)

from control_store import (
    get_run_history,
    get_run_detail
)

from run_metrics import (
    build_run_metrics
)


router = APIRouter(
    prefix="/runs",
    tags=["Run History"]
)


# ==========================================
# 1. 原有运行历史接口
# GET /runs
# ==========================================

@router.get(
    "",
    response_model=RunsResponse
)
def runs(
    limit: int = Query(
        default=20,
        ge=1,
        le=100
    )
):

    records = get_run_history(
        limit=limit
    )

    return {
        "count": len(records),
        "runs": records
    }


# ==========================================
# 2. 运行记录搜索接口
# POST /runs/search
# 今天新增 Depends
# ==========================================

@router.post(
    "/search",
    response_model=RunsResponse
)
def search_run_history(
    payload: RunSearchRequest,

    service: Annotated[
        RunSearchCallable,
        Depends(get_run_search_service)
    ]
):

    records = service(
        limit=payload.limit,
        min_event_count=payload.min_event_count,
        run_id_contains=payload.run_id_contains
    )

    return {
        "count": len(records),
        "runs": records
    }


# ==========================================
# 3. 原有运行详情接口
# GET /runs/{run_id}
# 今天使用自定义业务异常
# ==========================================

@router.get(
    "/{run_id}",
    response_model=RunDetailResponse
)
def run_detail(
    run_id: str,
    event_limit: int = Query(
        default=200,
        ge=1,
        le=1000
    )
):

    result = get_run_detail(
        run_id=run_id,
        event_limit=event_limit
    )

    if result is None:
        raise RunNotFoundError()

    return result


# ==========================================
# 4. 原有运行指标接口
# GET /runs/{run_id}/metrics
# ==========================================

@router.get("/{run_id}/metrics")
def run_metrics(
    run_id: str
):

    metrics = build_run_metrics(
        run_id
    )

    if metrics is None:
        raise RunNotFoundError()

    return metrics

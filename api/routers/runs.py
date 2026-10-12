
from fastapi import (
    APIRouter,
    HTTPException,
    Query
)

from api.schemas import (
    RunDetailResponse,
    RunSearchRequest,
    RunsResponse
)

from control_store import (
    get_run_history,
    get_run_detail
)

from run_metrics import (
    build_run_metrics
)

from run_search_service import (
    search_runs
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
# 2. 新增运行记录搜索接口
# POST /runs/search
# ==========================================

@router.post(
    "/search",
    response_model=RunsResponse
)
def search_run_history(
    payload: RunSearchRequest
):

    records = search_runs(
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
        raise HTTPException(
            status_code=404,
            detail="找不到该Run Trace"
        )

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
        raise HTTPException(
            status_code=404,
            detail="找不到该Run Trace"
        )

    return metrics

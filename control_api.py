from fastapi import (
    FastAPI,
    HTTPException,
    Query
)


from control_store import (
    get_active_goal,
    get_active_todos,
    get_current_quota,
    get_current_evidence,
    get_open_attention,
    get_current_acceptance,
    get_run_history,
    get_run_detail,
    get_overview
)

from run_metrics import (
    build_run_metrics
)

from dashboard_service import (
    build_dashboard
)

# ==========================================
# FastAPI App
# ==========================================

app = FastAPI(

    title=
        "LoopCoder Control Plane API",

    description=(
        "LoopCoder长程Coding Agent的"
        "只读Control Plane接口。"
        "\n\n"
        "用于查看Goal、Todo、Quota、"
        "Evidence、Attention和Run History。"
    ),

    version=
        "0.1.0"
)


# ==========================================
# Health
# ==========================================

@app.get(
    "/health",
    tags=[
        "System"
    ]
)
def health():

    return {

        "status":
            "ok",

        "service":
            "loopcoder-control-plane"
    }


# ==========================================
# Overview
# ==========================================

@app.get(
    "/control/overview",
    tags=[
        "Control Plane"
    ]
)
def control_overview():

    return (
        get_overview()
    )


# ==========================================
# Active Goal
# ==========================================

@app.get(
    "/goals/active",
    tags=[
        "Goal"
    ]
)
def active_goal():

    goal = (
        get_active_goal()
    )


    if goal is None:

        raise HTTPException(

            status_code=404,

            detail=(
                "当前没有Active Goal"
            )
        )


    return goal


# ==========================================
# Todos
# ==========================================

@app.get(
    "/goals/active/todos",
    tags=[
        "Goal"
    ]
)
def active_todos():

    goal = (
        get_active_goal()
    )


    if goal is None:

        raise HTTPException(

            status_code=404,

            detail=(
                "当前没有Active Goal"
            )
        )


    return {

        "goal_id":
            goal.get(
                "goal_id"
            ),

        "todos":
            get_active_todos()
    }


# ==========================================
# Quota
# ==========================================

@app.get(
    "/quota/current",
    tags=[
        "Quota"
    ]
)
def current_quota():

    quota = (
        get_current_quota()
    )


    if quota is None:

        return {

            "available":
                False,

            "reason":
                (
                    "当前没有Checkpoint。"
                    "已完成任务通常会清除Checkpoint，"
                    "因此可能不存在Current Quota。"
                ),

            "quota":
                None
        }


    return {

        "available":
            True,

        "quota":
            quota
    }


# ==========================================
# Evidence
# ==========================================

@app.get(
    "/evidence/current",
    tags=[
        "Evidence"
    ]
)
def current_evidence():

    goal = (
        get_active_goal()
    )


    if goal is None:

        raise HTTPException(

            status_code=404,

            detail=
                "当前没有Active Goal"
        )


    records = (
        get_current_evidence()
    )


    return {

        "goal_id":
            goal.get(
                "goal_id"
            ),

        "count":
            len(
                records
            ),

        "records":
            records
    }


# ==========================================
# Attention Queue
# ==========================================

@app.get(
    "/attention/current",
    tags=[
        "Attention"
    ]
)
def current_attention():

    goal = (
        get_active_goal()
    )


    records = (
        get_open_attention()
    )


    return {

        "goal_id":

            (
                goal.get(
                    "goal_id"
                )

                if goal

                else None
            ),

        "count":
            len(
                records
            ),

        "records":
            records
    }


# ==========================================
# Acceptance
# ==========================================

@app.get(
    "/acceptance/current",
    tags=[
        "Acceptance"
    ]
)
def current_acceptance():

    goal = (
        get_active_goal()
    )


    if goal is None:

        raise HTTPException(

            status_code=404,

            detail=
                "当前没有Active Goal"
        )


    record = (
        get_current_acceptance()
    )


    return {

        "goal_id":
            goal.get(
                "goal_id"
            ),

        "runtime_accepted":
            bool(
                goal.get(
                    "accepted",
                    False
                )
            ),

        "writeback":
            record
    }


# ==========================================
# Run History
# ==========================================

@app.get(
    "/runs",
    tags=[
        "Run History"
    ]
)
def runs(

    limit: int = Query(

        default=20,

        ge=1,

        le=100
    )
):

    records = (
        get_run_history(
            limit=limit
        )
    )


    return {

        "count":
            len(
                records
            ),

        "runs":
            records
    }


# ==========================================
# Run Detail
# ==========================================

@app.get(
    "/runs/{run_id}",
    tags=[
        "Run History"
    ]
)
def run_detail(

    run_id: str,

    event_limit: int = Query(

        default=200,

        ge=1,

        le=1000
    )
):

    result = (
        get_run_detail(

            run_id=
                run_id,

            event_limit=
                event_limit
        )
    )


    if result is None:

        raise HTTPException(

            status_code=404,

            detail=
                "找不到该Run Trace"
        )


    return result

# ==========================================
# Run Metrics
# ==========================================

@app.get(
    "/runs/{run_id}/metrics",
    tags=[
        "Run History"
    ]
)
def run_metrics(
    run_id: str
):

    metrics = (
        build_run_metrics(
            run_id
        )
    )


    if metrics is None:

        raise HTTPException(

            status_code=404,

            detail=
                "找不到该Run Trace"
        )


    return metrics
# ==========================================
# Dashboard
# ==========================================

@app.get(
    "/dashboard",
    tags=[
        "Dashboard"
    ]
)
def dashboard():

    return (
        build_dashboard()
    )
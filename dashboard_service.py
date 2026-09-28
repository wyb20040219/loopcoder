from control_store import (
    get_active_goal,
    get_active_todos,
    get_current_quota,
    get_current_evidence,
    get_open_attention,
    get_current_acceptance,
    get_run_history
)

from run_metrics import (
    build_run_metrics
)


# ==========================================
# Todo统计
# ==========================================

def build_todo_summary(
    todos: list[dict]
) -> dict:

    summary = {
        "TODO": 0,
        "RUNNING": 0,
        "BLOCKED": 0,
        "DONE": 0
    }


    for todo in todos:

        status = str(

            todo.get(
                "status",
                "TODO"
            )

        ).upper()


        if status in summary:

            summary[
                status
            ] += 1


    return summary


# ==========================================
# Evidence统计
# ==========================================

def build_evidence_summary(
    records: list
) -> dict:

    total = (
        len(
            records
        )
    )

    passed = 0

    failed = 0


    for record in records:

        if not isinstance(
            record,
            dict
        ):

            continue


        # 兼容：
        # passed=True/False
        # 或 status=PASS/FAIL
        record_passed = (
            record.get(
                "passed"
            )
        )


        if record_passed is True:

            passed += 1

            continue


        if record_passed is False:

            failed += 1

            continue


        status = str(

            record.get(
                "status",
                ""
            )

        ).upper()


        if status == "PASS":

            passed += 1


        elif status == "FAIL":

            failed += 1


    return {
        "total": total,
        "passed": passed,
        "failed": failed
    }


# ==========================================
# Dashboard
# ==========================================

def build_dashboard() -> dict:

    # ======================================
    # 当前Goal
    # ======================================

    goal = (
        get_active_goal()
    )


    # ======================================
    # Todo
    # ======================================

    todos = (
        get_active_todos()
    )


    todo_summary = (
        build_todo_summary(
            todos
        )
    )


    # ======================================
    # Quota
    # ======================================

    quota = (
        get_current_quota()
    )


    # ======================================
    # Evidence
    # ======================================

    evidence = (
        get_current_evidence()
    )


    evidence_summary = (
        build_evidence_summary(
            evidence
        )
    )


    # ======================================
    # Attention
    # ======================================

    attention = (
        get_open_attention()
    )


    # ======================================
    # Acceptance
    # ======================================

    acceptance = (
        get_current_acceptance()
    )


    # ======================================
    # 最新Run
    # ======================================

    runs = (
        get_run_history(
            limit=1
        )
    )


    latest_run = (

        runs[0]

        if runs

        else None
    )


    # ======================================
    # 最新Run Metrics
    # ======================================

    latest_metrics = None


    if latest_run is not None:

        run_id = (
            latest_run.get(
                "run_id"
            )
        )


        if run_id:

            latest_metrics = (
                build_run_metrics(
                    run_id
                )
            )


    # ======================================
    # Dashboard状态
    # ======================================

    if goal is None:

        system_state = (
            "IDLE"
        )


    elif (
        goal.get(
            "status"
        )
        ==
        "BLOCKED"
    ):

        system_state = (
            "NEEDS_ATTENTION"
        )


    elif (
        len(
            attention
        )
        >
        0
    ):

        system_state = (
            "NEEDS_ATTENTION"
        )


    elif (
        goal.get(
            "status"
        )
        ==
        "DONE"
    ):

        system_state = (
            "COMPLETED"
        )


    else:

        system_state = (
            "RUNNING"
        )


    # ======================================
    # 最终统一返回
    # ======================================

    return {

        "system_state":
            system_state,

        "goal":
            goal,

        "todos": {
            "summary":
                todo_summary,

            "items":
                todos
        },

        "quota":
            quota,

        "evidence": {
            "summary":
                evidence_summary,

            "records":
                evidence
        },

        "attention": {
            "count":
                len(
                    attention
                ),

            "items":
                attention
        },

        "acceptance":
            acceptance,

        "latest_run":
            latest_run,

        "latest_run_metrics":
            latest_metrics
    }
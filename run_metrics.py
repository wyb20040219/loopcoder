from datetime import (
    datetime
)


from control_store import (
    find_trace_by_run_id,
    read_trace_events
)


# ==========================================
# ISO时间解析
# ==========================================

def parse_time(
    value: str | None
):

    if not value:

        return None


    try:

        return (
            datetime.fromisoformat(
                value
            )
        )


    except Exception:

        return None


# ==========================================
# 判断Verification是否失败
#
# 当前Trace中的tool_result.result
# 保存的是字符串，所以这里做兼容解析。
# ==========================================

def verification_failed(
    result
) -> bool:

    text = str(
        result
    ).lower()


    return (

        "'passed': false"
        in text

        or

        '"passed": false'
        in text

        or

        "'status': 'test_failed'"
        in text

        or

        '"status": "test_failed"'
        in text
    )


# ==========================================
# 单次Run Metrics
# ==========================================

def build_run_metrics(
    run_id: str
):

    path = (
        find_trace_by_run_id(
            run_id
        )
    )


    if path is None:

        return None


    events = (
        read_trace_events(
            path
        )
    )


    metrics = {

        "run_id":
            run_id,

        "ticks":
            0,

        "llm_calls":
            0,

        "tool_calls":
            0,

        "verify_calls":
            0,

        "verify_failures":
            0,

        "approval_requests":
            0,

        "approval_denied":
            0,

        "tool_usage":
            {},

        "event_count":
            len(
                events
            ),

        "started_at":
            None,

        "ended_at":
            None,

        "duration_seconds":
            None
    }


    # ======================================
    # 没有事件
    # ======================================

    if not events:

        return metrics


    metrics[
        "started_at"
    ] = events[0].get(
        "time"
    )


    metrics[
        "ended_at"
    ] = events[-1].get(
        "time"
    )


    # ======================================
    # 遍历Trace
    # ======================================

    for event in events:

        event_type = (
            event.get(
                "event_type"
            )
        )


        data = (
            event.get(
                "data",
                {}
            )
        )


        # ==================================
        # Control Tick
        # ==================================

        if (
            event_type
            ==
            "control_decision"
        ):

            if data.get(
                "should_run",
                False
            ):

                metrics[
                    "ticks"
                ] += 1


        # ==================================
        # LLM
        # ==================================

        elif (
            event_type
            ==
            "llm_response"
        ):

            metrics[
                "llm_calls"
            ] += 1


        # ==================================
        # Approval
        # ==================================

        elif (
            event_type
            ==
            "approval_decision"
        ):

            metrics[
                "approval_requests"
            ] += 1


            if not data.get(
                "approved",
                False
            ):

                metrics[
                    "approval_denied"
                ] += 1


        # ==================================
        # Tool
        # ==================================

        elif (
            event_type
            ==
            "tool_result"
        ):

            metrics[
                "tool_calls"
            ] += 1


            tool_name = str(

                data.get(
                    "tool_name",
                    "unknown"
                )
            )


            metrics[
                "tool_usage"
            ][
                tool_name
            ] = (

                metrics[
                    "tool_usage"
                ].get(
                    tool_name,
                    0
                )

                +
                1
            )


            # ==============================
            # Verification
            # ==============================

            if (
                tool_name
                ==
                "verify_project"
            ):

                metrics[
                    "verify_calls"
                ] += 1


                if (
                    verification_failed(
                        data.get(
                            "result"
                        )
                    )
                ):

                    metrics[
                        "verify_failures"
                    ] += 1


    # ======================================
    # Duration
    # ======================================

    start = (
        parse_time(
            metrics[
                "started_at"
            ]
        )
    )


    end = (
        parse_time(
            metrics[
                "ended_at"
            ]
        )
    )


    if (
        start is not None
        and
        end is not None
    ):

        metrics[
            "duration_seconds"
        ] = round(

            (
                end
                -
                start
            ).total_seconds(),

            2
        )


    return metrics
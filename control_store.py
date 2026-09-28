import json

from pathlib import Path


# ==========================================
# 基础目录
# ==========================================

BASE_DIR = Path(
    __file__
).resolve().parent


GOALS_DIR = (
    BASE_DIR
    /
    "goals"
)


EVIDENCE_DIR = (
    BASE_DIR
    /
    "evidence"
)


ATTENTION_DIR = (
    BASE_DIR
    /
    "attention"
)


CHECKPOINT_DIR = (
    BASE_DIR
    /
    "checkpoints"
)


ACCEPTED_DIR = (
    BASE_DIR
    /
    "accepted"
)


TRACE_DIR = (
    BASE_DIR
    /
    "traces"
)


# ==========================================
# 固定状态文件
# ==========================================

ACTIVE_GOAL_PATH = (
    GOALS_DIR
    /
    "active_goal.json"
)


CHECKPOINT_PATH = (
    CHECKPOINT_DIR
    /
    "agent_checkpoint.json"
)


ATTENTION_PATH = (
    ATTENTION_DIR
    /
    "queue.json"
)


# ==========================================
# JSON安全读取
# ==========================================

def read_json_file(
    path: Path
):

    if not path.exists():

        return None


    try:

        return json.loads(

            path.read_text(
                encoding="utf-8"
            )
        )


    except Exception as e:

        return {

            "_read_error":
                str(e),

            "_path":
                str(path)
        }


# ==========================================
# Active Goal
# ==========================================

def get_active_goal() -> dict | None:

    data = (
        read_json_file(
            ACTIVE_GOAL_PATH
        )
    )


    if not isinstance(
        data,
        dict
    ):

        return None


    return data


# ==========================================
# Todos
# ==========================================

def get_active_todos() -> list[dict]:

    goal = (
        get_active_goal()
    )


    if goal is None:

        return []


    todos = (
        goal.get(
            "todos",
            []
        )
    )


    if not isinstance(
        todos,
        list
    ):

        return []


    return todos


# ==========================================
# Current Checkpoint
# ==========================================

def get_checkpoint() -> dict | None:

    data = (
        read_json_file(
            CHECKPOINT_PATH
        )
    )


    if not isinstance(
        data,
        dict
    ):

        return None


    return data


# ==========================================
# Current Quota
#
# Quota被保存在Checkpoint里。
#
# 已完成任务可能已经clear checkpoint，
# 因此这里允许返回None。
# ==========================================

def get_current_quota():

    checkpoint = (
        get_checkpoint()
    )


    if checkpoint is None:

        return None


    return checkpoint.get(
        "quota_state"
    )


# ==========================================
# Evidence数据兼容处理
#
# 支持：
#
# [
#   {...},
#   {...}
# ]
#
# 或：
#
# {
#   "records": [...]
# }
# ==========================================

def normalize_record_list(
    data,
    candidate_keys: tuple[str, ...]
) -> list:

    if isinstance(
        data,
        list
    ):

        return data


    if isinstance(
        data,
        dict
    ):

        for key in (
            candidate_keys
        ):

            value = (
                data.get(
                    key
                )
            )


            if isinstance(
                value,
                list
            ):

                return value


    return []


# ==========================================
# Current Goal Evidence
# ==========================================

def get_current_evidence() -> list:

    goal = (
        get_active_goal()
    )


    if goal is None:

        return []


    goal_id = (
        goal.get(
            "goal_id"
        )
    )


    if not goal_id:

        return []


    path = (

        EVIDENCE_DIR
        /
        f"{goal_id}.json"
    )


    data = (
        read_json_file(
            path
        )
    )


    return normalize_record_list(

        data,

        (
            "records",
            "evidence",
            "items"
        )
    )


# ==========================================
# Attention Queue
# ==========================================

def get_attention_items() -> list:

    data = (
        read_json_file(
            ATTENTION_PATH
        )
    )


    return normalize_record_list(

        data,

        (
            "items",
            "records",
            "queue"
        )
    )


# ==========================================
# 当前Goal的OPEN Attention
# ==========================================

def get_open_attention() -> list:

    goal = (
        get_active_goal()
    )


    goal_id = (

        goal.get(
            "goal_id"
        )

        if goal

        else None
    )


    items = (
        get_attention_items()
    )


    result = []


    for item in items:

        if not isinstance(
            item,
            dict
        ):

            continue


        # ==================================
        # 如果Attention记录有goal_id，
        # 只显示当前Goal。
        #
        # 如果旧格式没有goal_id，
        # 也允许显示。
        # ==================================

        item_goal_id = (
            item.get(
                "goal_id"
            )
        )


        if (
            goal_id

            and

            item_goal_id

            and

            item_goal_id
            !=
            goal_id
        ):

            continue


        status = str(

            item.get(
                "status",
                "OPEN"
            )

        ).upper()


        if (
            status
            ==
            "OPEN"
        ):

            result.append(
                item
            )


    return result


# ==========================================
# Accepted Writeback
# ==========================================

def get_current_acceptance():

    goal = (
        get_active_goal()
    )


    if goal is None:

        return None


    goal_id = (
        goal.get(
            "goal_id"
        )
    )


    if not goal_id:

        return None


    path = (

        ACCEPTED_DIR
        /
        f"{goal_id}.json"
    )


    return (
        read_json_file(
            path
        )
    )


# ==========================================
# Trace读取
# ==========================================

def read_trace_events(
    path: Path,
    limit: int | None = None
) -> list[dict]:

    events = []


    if not path.exists():

        return events


    try:

        with path.open(

            "r",

            encoding="utf-8"

        ) as f:

            for line in f:

                line = (
                    line.strip()
                )


                if not line:

                    continue


                try:

                    event = (
                        json.loads(
                            line
                        )
                    )


                except json.JSONDecodeError:

                    continue


                events.append(
                    event
                )


    except Exception:

        return []


    # ======================================
    # API只返回最后N条
    # 防止Trace太大
    # ======================================

    if (
        limit is not None

        and

        limit > 0
    ):

        events = (
            events[
                -limit:
            ]
        )


    return events


# ==========================================
# 单个Trace摘要
# ==========================================

def build_trace_summary(
    path: Path
) -> dict:

    events = (
        read_trace_events(
            path
        )
    )


    event_counts = {}


    for event in events:

        event_type = str(

            event.get(
                "event_type",
                "unknown"
            )
        )


        event_counts[
            event_type
        ] = (

            event_counts.get(
                event_type,
                0
            )

            +
            1
        )


    started_at = (

        events[0].get(
            "time"
        )

        if events

        else None
    )


    ended_at = (

        events[-1].get(
            "time"
        )

        if events

        else None
    )


    return {

        "run_id":
            path.stem,

        "file_name":
            path.name,

        "started_at":
            started_at,

        "ended_at":
            ended_at,

        "event_count":
            len(
                events
            ),

        "event_counts":
            event_counts
    }


# ==========================================
# Run History
# ==========================================

def get_run_history(
    limit: int = 20
) -> list[dict]:

    if not TRACE_DIR.exists():

        return []


    paths = list(

        TRACE_DIR.glob(
            "*.jsonl"
        )
    )


    paths.sort(

        key=lambda path:
            path.stat().st_mtime,

        reverse=True
    )


    paths = (
        paths[
            :limit
        ]
    )


    return [

        build_trace_summary(
            path
        )

        for path
        in paths
    ]


# ==========================================
# 根据run_id找Trace
#
# 不允许用户直接传路径。
#
# 这样避免：
#
# ../../xxx
#
# Path Traversal
# ==========================================

def find_trace_by_run_id(
    run_id: str
) -> Path | None:

    if not TRACE_DIR.exists():

        return None


    for path in (

        TRACE_DIR.glob(
            "*.jsonl"
        )
    ):

        if (
            path.stem
            ==
            run_id
        ):

            return path


    return None


# ==========================================
# Run Detail
# ==========================================

def get_run_detail(
    run_id: str,
    event_limit: int = 200
):

    path = (
        find_trace_by_run_id(
            run_id
        )
    )


    if path is None:

        return None


    summary = (
        build_trace_summary(
            path
        )
    )


    events = (
        read_trace_events(

            path=

                path,

            limit=
                event_limit
        )
    )


    return {

        "summary":
            summary,

        "events":
            events
    }


# ==========================================
# Overview
#
# 给未来Dashboard一个接口就能拿到
# 当前Control Plane核心状态。
# ==========================================

def get_overview() -> dict:

    goal = (
        get_active_goal()
    )


    todos = (
        get_active_todos()
    )


    evidence = (
        get_current_evidence()
    )


    attention = (
        get_open_attention()
    )


    quota = (
        get_current_quota()
    )


    acceptance = (
        get_current_acceptance()
    )


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


    todo_counts = {

        "TODO":
            0,

        "RUNNING":
            0,

        "BLOCKED":
            0,

        "DONE":
            0
    }


    for todo in todos:

        status = str(

            todo.get(
                "status",
                "TODO"
            )

        ).upper()


        if (
            status
            in
            todo_counts
        ):

            todo_counts[
                status
            ] += 1


    return {

        "goal":
            goal,

        "todo_summary":
            todo_counts,

        "quota":
            quota,

        "evidence_count":
            len(
                evidence
            ),

        "open_attention_count":
            len(
                attention
            ),

        "accepted":
            bool(

                goal
                and
                goal.get(
                    "accepted",
                    False
                )
            ),

        "acceptance":
            acceptance,

        "latest_run":
            latest_run
    }
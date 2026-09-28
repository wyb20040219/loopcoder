import csv
import json
import os
import sys
import time

from datetime import datetime
from pathlib import Path


from llm_rate_limiter import (
    get_total_wait_seconds,
    reset_rate_limiter
)


# ==========================================
# 基础路径
# ==========================================

BASE_DIR = Path(
    __file__
).resolve().parent


CASES_PATH = (

    BASE_DIR
    /
    "benchmarks"
    /
    "day76_cases.json"
)


RESULTS_DIR = (

    BASE_DIR
    /
    "benchmarks"
    /
    "day76_results"
)


RESULTS_DIR.mkdir(
    parents=True,
    exist_ok=True
)


TRACE_DIR = (

    BASE_DIR
    /
    "traces"
)


# ==========================================
# 加载Benchmark Cases
# ==========================================

def load_cases() -> list[dict]:

    if not CASES_PATH.exists():

        raise FileNotFoundError(

            "找不到Day76 Benchmark配置："
            f"{CASES_PATH}"
        )


    content = (

        CASES_PATH.read_text(
            encoding="utf-8"
        )
    )


    return json.loads(
        content
    )


# ==========================================
# 清理LoopCoder旧运行状态
# ==========================================

def clear_loopcoder_state():

    paths = [

        (
            BASE_DIR
            /
            "checkpoints"
            /
            "agent_checkpoint.json"
        ),

        (
            BASE_DIR
            /
            "goals"
            /
            "active_goal.json"
        )
    ]


    for path in paths:

        if path.exists():

            path.unlink()


# ==========================================
# 当前Trace文件集合
# ==========================================

def get_trace_files() -> set[Path]:

    if not TRACE_DIR.exists():

        return set()


    return set(

        TRACE_DIR.glob(
            "*.jsonl"
        )
    )


# ==========================================
# 找出本次LoopCoder新产生的Trace
# ==========================================

def find_new_trace(
    before: set[Path]
) -> Path | None:

    after = (
        get_trace_files()
    )


    new_files = (

        after
        -
        before
    )


    if not new_files:

        return None


    return max(

        new_files,

        key=lambda path:
            path.stat().st_mtime
    )


# ==========================================
# 从LoopCoder Trace中提取Metrics
# ==========================================

def parse_loopcoder_trace(
    trace_path: Path | None
) -> dict:

    metrics = {

        "steps":
            0,

        "llm_calls":
            0,

        "tool_calls":
            0,

        "verify_calls":
            0,

        "verify_failures":
            0
    }


    if (
        trace_path is None
        or
        not trace_path.exists()
    ):

        return metrics


    with trace_path.open(
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
                        "steps"
                    ] += 1


            # ==================================
            # LLM调用
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
            # Tool调用
            # ==================================

            elif (
                event_type
                ==
                "tool_result"
            ):

                metrics[
                    "tool_calls"
                ] += 1


                if (
                    data.get(
                        "tool_name"
                    )
                    ==
                    "verify_project"
                ):

                    metrics[
                        "verify_calls"
                    ] += 1


                    result_text = str(

                        data.get(
                            "result",
                            ""
                        )
                    )


                    normalized = (
                        result_text.lower()
                    )


                    if (

                        "'passed': false"
                        in normalized

                        or

                        '"passed": false'
                        in normalized
                    ):

                        metrics[
                            "verify_failures"
                        ] += 1


    return metrics


# ==========================================
# 读取LoopCoder内部是否Accepted
# ==========================================

def read_runtime_accepted() -> bool:

    path = (

        BASE_DIR
        /
        "goals"
        /
        "active_goal.json"
    )


    if not path.exists():

        return False


    try:

        data = json.loads(

            path.read_text(
                encoding="utf-8"
            )
        )


        return bool(

            data.get(
                "accepted",
                False
            )
        )


    except Exception:

        return False


# ==========================================
# 文件变化判定
# ==========================================

def evaluate_changed_files(
    changed_files: list[str],
    allowed_changes: list[str],
    protected_paths: list[str]
) -> dict:

    normalized_changed = [

        item
        .replace("\\", "/")
        .strip("/")

        for item
        in changed_files
    ]


    normalized_allowed = {

        item
        .replace("\\", "/")
        .strip("/")

        for item
        in allowed_changes
    }


    normalized_protected = [

        item
        .replace("\\", "/")
        .strip("/")

        for item
        in protected_paths
    ]


    protected_violations = []


    # ======================================
    # Protected Paths检查
    # ======================================

    for path in normalized_changed:

        for protected in (
            normalized_protected
        ):

            if (

                path
                ==
                protected

                or

                path.startswith(
                    protected
                    +
                    "/"
                )
            ):

                protected_violations.append(
                    path
                )


    # ======================================
    # Unexpected Changes检查
    #
    # Day76当前采用精确Allowed File列表
    # ======================================

    unexpected_changes = [

        path

        for path
        in normalized_changed

        if path not in (
            normalized_allowed
        )
    ]


    return {

        "protected_violations":
            sorted(
                set(
                    protected_violations
                )
            ),

        "unexpected_changes":
            sorted(
                set(
                    unexpected_changes
                )
            )
    }


# ==========================================
# Independent Evaluator
#
# Agent = 考生
#
# 这里 = 外部考官
# ==========================================

def independently_evaluate(
    case: dict
) -> dict:

    from verification import (
        verify_command
    )

    from protection import (
        get_changed_files
    )


    # ======================================
    # Evaluator始终使用真实Protected规则
    #
    # 即使Bare运行时没有硬保护，
    # 最终判卷规则仍然相同。
    # ======================================

    os.environ[
        "AGENT_PROTECTED_PATHS"
    ] = json.dumps(

        case[
            "protected_paths"
        ]
    )


    # ======================================
    # 独立再次运行pytest
    # ======================================

    verification = (
        verify_command(

            command=
                case[
                    "verify_command"
                ],

            timeout=60
        )
    )


    # ======================================
    # 独立检查Git Workspace变化
    # ======================================

    changed_result = (
        get_changed_files()
    )


    if changed_result.get(
        "success",
        False
    ):

        changed_files = (
            changed_result.get(
                "files",
                []
            )
        )


    else:

        changed_files = []


    change_eval = (
        evaluate_changed_files(

            changed_files=
                changed_files,

            allowed_changes=
                case[
                    "allowed_changes"
                ],

            protected_paths=
                case[
                    "protected_paths"
                ]
        )
    )


    # ======================================
    # Benchmark最终Pass规则
    #
    # 1. 独立pytest PASS
    # 2. 确实产生代码变化
    # 3. 没改Protected Files
    # 4. 没有Unexpected Changes
    # ======================================

    benchmark_passed = (

        verification.get(
            "passed",
            False
        )

        and

        len(
            changed_files
        )
        >
        0

        and

        not change_eval[
            "protected_violations"
        ]

        and

        not change_eval[
            "unexpected_changes"
        ]
    )


    return {

        "benchmark_passed":
            benchmark_passed,

        "verification":
            verification,

        "changed_files":
            changed_files,

        "protected_violations":
            change_eval[
                "protected_violations"
            ],

        "unexpected_changes":
            change_eval[
                "unexpected_changes"
            ]
    }


# ==========================================
# Bare Agent Benchmark
# ==========================================

def run_bare_case(
    case: dict
) -> dict:

    from workspace_manager import (
        prepare_run
    )

    from bare_agent import (
        run_bare_agent
    )


    source_repo = (

        BASE_DIR
        /
        case[
            "source_repo"
        ]
    ).resolve()


    # ======================================
    # 每个系统使用独立Run Workspace
    # ======================================

    run = (
        prepare_run(
            source_repo
        )
    )


    os.environ[
        "AGENT_WORKSPACE"
    ] = str(
        run[
            "workspace"
        ]
    )


    # ======================================
    # Bare Agent：
    #
    # 不开启Protected Path硬拦截。
    #
    # 它只有Prompt中的：
    #
    # "不要修改tests"
    # ======================================

    os.environ[
        "AGENT_PROTECTED_PATHS"
    ] = "[]"


    # ======================================
    # Rate Limiter时间快照
    # ======================================

    rate_wait_before = (
        get_total_wait_seconds()
    )


    start = (
        time.perf_counter()
    )


    error = None


    try:

        bare_result = (
            run_bare_agent(

                user_task=
                    case[
                        "task"
                    ],

                max_steps=
                    case[
                        "max_steps"
                    ]
            )
        )


        # ==================================
        # Bare Agent内部可能捕获了LLM异常
        #
        # 但Metrics不会丢失
        # ==================================

        error = (
            bare_result.get(
                "agent_error"
            )
        )


    except Exception as e:

        # ==================================
        # 这里只处理Bare Agent之外
        # 不可预期的Runner错误
        # ==================================

        error = (

            f"{type(e).__name__}: "
            f"{e}"
        )


        bare_result = {

            "verified":
                False,

            "final_text":
                "",

            "agent_error":
                error,

            "metrics": {

                "steps":
                    0,

                "llm_calls":
                    0,

                "tool_calls":
                    0,

                "verify_calls":
                    0,

                "verify_failures":
                    0
            }
        }


    elapsed = (

        time.perf_counter()
        -
        start
    )


    rate_wait_after = (
        get_total_wait_seconds()
    )


    rate_limit_wait_seconds = (

        rate_wait_after
        -
        rate_wait_before
    )


    active_seconds = max(

        0.0,

        elapsed
        -
        rate_limit_wait_seconds
    )


    # ======================================
    # 独立Evaluator
    # ======================================

    evaluation = (
        independently_evaluate(
            case
        )
    )


    metrics = (
        bare_result[
            "metrics"
        ]
    )


    return {

        "system":
            "bare",

        "case_id":
            case[
                "id"
            ],

        "run_id":
            run[
                "run_id"
            ],

        "workspace":
            str(
                run[
                    "workspace"
                ]
            ),

        "benchmark_passed":
            (
                error is None
                and
                evaluation[
                    "benchmark_passed"
                ]
            ),

        # ==================================
        # Bare不存在LoopCoder内部Acceptance
        # ==================================

        "runtime_accepted":
            None,

        "agent_error":
            error,

        "elapsed_seconds":
            round(
                elapsed,
                2
            ),

        "rate_limit_wait_seconds":
            round(
                rate_limit_wait_seconds,
                2
            ),

        "active_seconds":
            round(
                active_seconds,
                2
            ),

        "steps":
            metrics[
                "steps"
            ],

        "llm_calls":
            metrics[
                "llm_calls"
            ],

        "tool_calls":
            metrics[
                "tool_calls"
            ],

        "verify_calls":
            metrics[
                "verify_calls"
            ],

        "verify_failures":
            metrics[
                "verify_failures"
            ],

        # ==================================
        # 至少出现一次Verify失败
        # 最终却通过
        #
        # 才算Recovery Success
        # ==================================

        "recovery_success":
            (
                metrics[
                    "verify_failures"
                ]
                >
                0

                and

                evaluation[
                    "benchmark_passed"
                ]
            ),

        "changed_files":
            evaluation[
                "changed_files"
            ],

        "protected_violations":
            evaluation[
                "protected_violations"
            ],

        "unexpected_changes":
            evaluation[
                "unexpected_changes"
            ],

        "verification":
            evaluation[
                "verification"
            ],

        "final_answer":
            bare_result.get(
                "final_text",
                ""
            )
    }


# ==========================================
# LoopCoder Benchmark
# ==========================================

def run_loopcoder_case(
    case: dict
) -> dict:

    from workspace_manager import (
        prepare_run
    )

    from agent import (
        run_agent
    )


    source_repo = (

        BASE_DIR
        /
        case[
            "source_repo"
        ]
    ).resolve()


    # ======================================
    # 独立Run Workspace
    # ======================================

    run = (
        prepare_run(
            source_repo
        )
    )


    os.environ[
        "AGENT_WORKSPACE"
    ] = str(
        run[
            "workspace"
        ]
    )


    # ======================================
    # LoopCoder开启真正Protected Paths
    # ======================================

    os.environ[
        "AGENT_PROTECTED_PATHS"
    ] = json.dumps(

        case[
            "protected_paths"
        ]
    )


    # ======================================
    # Benchmark不能等待人工输入
    # ======================================

    os.environ[
        "AGENT_APPROVAL_MODE"
    ] = "auto"


    # ======================================
    # 防止上一次Goal / Checkpoint污染
    # ======================================

    clear_loopcoder_state()


    # ======================================
    # 记录Run之前已有Trace
    # ======================================

    trace_before = (
        get_trace_files()
    )


    # ======================================
    # Rate Limiter统计
    # ======================================

    rate_wait_before = (
        get_total_wait_seconds()
    )


    start = (
        time.perf_counter()
    )


    error = None

    final_answer = ""


    try:

        final_answer = (
            run_agent(

                user_task=
                    case[
                        "task"
                    ],

                max_ticks=
                    case[
                        "max_steps"
                    ],

                max_llm_calls=
                    case[
                        "max_steps"
                    ],

                max_tool_calls=
                    50,

                max_verify_calls=
                    6,

                max_runtime_seconds=
                    900
            )
        )


    except Exception as e:

        error = (

            f"{type(e).__name__}: "
            f"{e}"
        )


        print(
            "\n[LoopCoder] Agent异常："
        )


        print(
            error
        )


    elapsed = (

        time.perf_counter()
        -
        start
    )


    rate_wait_after = (
        get_total_wait_seconds()
    )


    rate_limit_wait_seconds = (

        rate_wait_after
        -
        rate_wait_before
    )


    active_seconds = max(

        0.0,

        elapsed
        -
        rate_limit_wait_seconds
    )


    # ======================================
    # 找本次Run Trace
    # ======================================

    trace_path = (
        find_new_trace(
            trace_before
        )
    )


    metrics = (
        parse_loopcoder_trace(
            trace_path
        )
    )


    runtime_accepted = (
        read_runtime_accepted()
    )


    # ======================================
    # 外部独立Evaluator
    # ======================================

    evaluation = (
        independently_evaluate(
            case
        )
    )


    return {

        "system":
            "loopcoder",

        "case_id":
            case[
                "id"
            ],

        "run_id":
            run[
                "run_id"
            ],

        "workspace":
            str(
                run[
                    "workspace"
                ]
            ),

        "benchmark_passed":
            (
                error is None
                and
                evaluation[
                    "benchmark_passed"
                ]
            ),

        "runtime_accepted":
            runtime_accepted,

        "agent_error":
            error,

        "elapsed_seconds":
            round(
                elapsed,
                2
            ),

        "rate_limit_wait_seconds":
            round(
                rate_limit_wait_seconds,
                2
            ),

        "active_seconds":
            round(
                active_seconds,
                2
            ),

        "steps":
            metrics[
                "steps"
            ],

        "llm_calls":
            metrics[
                "llm_calls"
            ],

        "tool_calls":
            metrics[
                "tool_calls"
            ],

        "verify_calls":
            metrics[
                "verify_calls"
            ],

        "verify_failures":
            metrics[
                "verify_failures"
            ],

        "recovery_success":
            (
                metrics[
                    "verify_failures"
                ]
                >
                0

                and

                evaluation[
                    "benchmark_passed"
                ]
            ),

        "changed_files":
            evaluation[
                "changed_files"
            ],

        "protected_violations":
            evaluation[
                "protected_violations"
            ],

        "unexpected_changes":
            evaluation[
                "unexpected_changes"
            ],

        "verification":
            evaluation[
                "verification"
            ],

        "trace_path":
            (
                str(
                    trace_path
                )

                if trace_path

                else

                None
            ),

        "final_answer":
            final_answer
    }


# ==========================================
# 汇总Benchmark结果
# ==========================================

def build_summary(
    results: list[dict]
) -> dict:

    summary = {}


    for system in (
        "bare",
        "loopcoder"
    ):

        rows = [

            item

            for item
            in results

            if item[
                "system"
            ]
            ==
            system
        ]


        if not rows:

            continue


        passed = sum(

            1

            for item
            in rows

            if item[
                "benchmark_passed"
            ]
        )


        summary[
            system
        ] = {

            "cases":
                len(
                    rows
                ),

            "passed":
                passed,

            # ==================================
            # 注意：
            #
            # 这是当前这些Case里的通过比例。
            #
            # 不是经过大量重复实验以后
            # 得到的概率意义成功率。
            # ==================================

            "case_pass_rate":
                round(

                    passed
                    /
                    len(
                        rows
                    ),

                    3
                ),

            "avg_llm_calls":
                round(

                    sum(
                        item[
                            "llm_calls"
                        ]

                        for item
                        in rows
                    )

                    /
                    len(
                        rows
                    ),

                    2
                ),

            "avg_tool_calls":
                round(

                    sum(
                        item[
                            "tool_calls"
                        ]

                        for item
                        in rows
                    )

                    /
                    len(
                        rows
                    ),

                    2
                ),

            "avg_verify_calls":
                round(

                    sum(
                        item[
                            "verify_calls"
                        ]

                        for item
                        in rows
                    )

                    /
                    len(
                        rows
                    ),

                    2
                ),

            "avg_verify_failures":
                round(

                    sum(
                        item[
                            "verify_failures"
                        ]

                        for item
                        in rows
                    )

                    /
                    len(
                        rows
                    ),

                    2
                ),

            # ==================================
            # 用户真实等待时间
            # ==================================

            "avg_elapsed_seconds":
                round(

                    sum(
                        item[
                            "elapsed_seconds"
                        ]

                        for item
                        in rows
                    )

                    /
                    len(
                        rows
                    ),

                    2
                ),

            # ==================================
            # 因Benchmark主动RPM节流等待
            # ==================================

            "avg_rate_limit_wait_seconds":
                round(

                    sum(
                        item[
                            "rate_limit_wait_seconds"
                        ]

                        for item
                        in rows
                    )

                    /
                    len(
                        rows
                    ),

                    2
                ),

            # ==================================
            # elapsed - 主动限流等待
            #
            # 更适合比较Runtime自身开销
            # ==================================

            "avg_active_seconds":
                round(

                    sum(
                        item[
                            "active_seconds"
                        ]

                        for item
                        in rows
                    )

                    /
                    len(
                        rows
                    ),

                    2
                ),

            "protected_violation_count":
                sum(

                    len(
                        item[
                            "protected_violations"
                        ]
                    )

                    for item
                    in rows
                ),

            "unexpected_change_count":
                sum(

                    len(
                        item[
                            "unexpected_changes"
                        ]
                    )

                    for item
                    in rows
                ),

            "recovery_success_count":
                sum(

                    1

                    for item
                    in rows

                    if item[
                        "recovery_success"
                    ]
                ),

            "agent_error_count":
                sum(

                    1

                    for item
                    in rows

                    if item.get(
                        "agent_error"
                    )
                    is not None
                )
        }


    return summary


# ==========================================
# 保存CSV
# ==========================================

def save_csv(
    results: list[dict],
    path: Path
):

    fields = [

        "system",

        "case_id",

        "benchmark_passed",

        "runtime_accepted",

        "agent_error",

        "elapsed_seconds",

        "rate_limit_wait_seconds",

        "active_seconds",

        "steps",

        "llm_calls",

        "tool_calls",

        "verify_calls",

        "verify_failures",

        "recovery_success",

        "changed_files",

        "protected_violations",

        "unexpected_changes"
    ]


    with path.open(

        "w",

        newline="",

        encoding="utf-8-sig"

    ) as f:

        writer = (
            csv.DictWriter(

                f,

                fieldnames=
                    fields
            )
        )


        writer.writeheader()


        for item in results:

            row = {

                field:
                    item.get(
                        field
                    )

                for field
                in fields
            }


            # ==================================
            # list写成JSON字符串
            # ==================================

            for field in (

                "changed_files",
                "protected_violations",
                "unexpected_changes"
            ):

                row[
                    field
                ] = json.dumps(

                    row.get(
                        field,
                        []
                    ),

                    ensure_ascii=False
                )


            writer.writerow(
                row
            )


# ==========================================
# 控制台打印单个结果
# ==========================================

def print_result(
    result: dict
):

    print(
        "\n"
        "--------------------------------"
    )


    print(

        f"{result['system']} | "
        f"{result['case_id']}"
    )


    print(
        "Passed:",
        result[
            "benchmark_passed"
        ]
    )


    print(
        "Runtime Accepted:",
        result[
            "runtime_accepted"
        ]
    )


    print(
        "Agent Error:",
        result[
            "agent_error"
        ]
    )


    print(
        "Steps:",
        result[
            "steps"
        ]
    )


    print(
        "LLM Calls:",
        result[
            "llm_calls"
        ]
    )


    print(
        "Tool Calls:",
        result[
            "tool_calls"
        ]
    )


    print(
        "Verify Calls:",
        result[
            "verify_calls"
        ]
    )


    print(
        "Verify Failures:",
        result[
            "verify_failures"
        ]
    )


    print(
        "Elapsed:",
        result[
            "elapsed_seconds"
        ]
    )


    print(
        "Rate Limit Wait:",
        result[
            "rate_limit_wait_seconds"
        ]
    )


    print(
        "Active Seconds:",
        result[
            "active_seconds"
        ]
    )


    print(
        "Changed Files:",
        result[
            "changed_files"
        ]
    )


    print(
        "Protected Violations:",
        result[
            "protected_violations"
        ]
    )


    print(
        "Unexpected Changes:",
        result[
            "unexpected_changes"
        ]
    )


    print(
        "Recovery Success:",
        result[
            "recovery_success"
        ]
    )


# ==========================================
# Main
# ==========================================

def main():

    # ======================================
    # Day76 Benchmark固定限速
    #
    # Moonshot：
    # 当前组织RPM约3。
    #
    # 21秒间隔≈2.86 requests/min
    #
    # 如果以后API额度提高，
    # 可以提前设置环境变量覆盖：
    #
    # AGENT_LLM_MIN_INTERVAL_SECONDS
    # ======================================

    os.environ.setdefault(

        "AGENT_LLM_MIN_INTERVAL_SECONDS",

        "21"
    )


    # ======================================
    # 每次启动新的Benchmark命令
    # 从一个干净的Limiter状态开始
    #
    # 注意：
    # Bare跑完以后不会再次reset，
    # 所以LoopCoder仍然继承共享节流窗口。
    # ======================================

    reset_rate_limiter()


    cases = (
        load_cases()
    )


    # ======================================
    # 参数：
    #
    # 不传：
    # all
    #
    # 或：
    #
    # duplicate_email
    # email_normalization
    # account_transfer
    # ======================================

    selected = (

        "all"

        if len(
            sys.argv
        )
        <
        2

        else

        sys.argv[
            1
        ]
        .strip()
    )


    if (
        selected
        !=
        "all"
    ):

        cases = [

            case

            for case
            in cases

            if case[
                "id"
            ]
            ==
            selected
        ]


        if not cases:

            print(
                f"找不到Case：{selected}"
            )


            print(
                "\n可用Case："
            )


            for case in (
                load_cases()
            ):

                print(
                    "-",
                    case[
                        "id"
                    ]
                )


            return


    results = []


    # ======================================
    # 正式Benchmark
    # ======================================

    for case in cases:

        print(
            "\n"
            "================================"
        )


        print(
            "Benchmark Case:",
            case[
                "id"
            ]
        )


        print(
            "================================"
        )


        # ==================================
        # A组：
        # Bare Agent
        # ==================================

        bare_result = (
            run_bare_case(
                case
            )
        )


        results.append(
            bare_result
        )


        print_result(
            bare_result
        )


        # ==================================
        # B组：
        # LoopCoder
        #
        # 注意：
        #
        # 不reset Rate Limiter。
        #
        # 因此它会自动等待Bare留下的
        # API时间窗口。
        # ==================================

        loopcoder_result = (
            run_loopcoder_case(
                case
            )
        )


        results.append(
            loopcoder_result
        )


        print_result(
            loopcoder_result
        )


    # ======================================
    # 汇总
    # ======================================

    summary = (
        build_summary(
            results
        )
    )


    timestamp = (
        datetime.now()
        .strftime(
            "%Y%m%d_%H%M%S"
        )
    )


    json_path = (

        RESULTS_DIR

        /

        (
            f"{timestamp}_"
            "benchmark.json"
        )
    )


    csv_path = (

        RESULTS_DIR

        /

        (
            f"{timestamp}_"
            "benchmark.csv"
        )
    )


    # ======================================
    # JSON
    # ======================================

    json_path.write_text(

        json.dumps(

            {

                "benchmark_config": {

                    "llm_min_interval_seconds":
                        float(
                            os.getenv(
                                "AGENT_LLM_MIN_INTERVAL_SECONDS",
                                "0"
                            )
                        ),

                    "selected_case":
                        selected
                },

                "results":
                    results,

                "summary":
                    summary
            },

            ensure_ascii=False,

            indent=2
        ),

        encoding="utf-8"
    )


    # ======================================
    # CSV
    # ======================================

    save_csv(
        results,
        csv_path
    )


    # ======================================
    # Console Summary
    # ======================================

    print(
        "\n"
        "================================"
    )


    print(
        "Day76 Benchmark Summary"
    )


    print(
        "================================"
    )


    print(
        json.dumps(
            summary,
            ensure_ascii=False,
            indent=2
        )
    )


    print(
        "\nJSON:"
    )


    print(
        json_path
    )


    print(
        "\nCSV:"
    )


    print(
        csv_path
    )


if __name__ == "__main__":

    main()
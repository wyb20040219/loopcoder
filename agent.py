import time

from uuid import (
    uuid4
)

from langchain_openai import (
    ChatOpenAI
)

from langchain_core.messages import (
    ToolMessage,
    HumanMessage
)

from openai import (
    RateLimitError,
    APITimeoutError,
    APIConnectionError
)

from config import (
    MOONSHOT_API_KEY,
    MOONSHOT_BASE_URL,
    MODEL_NAME
)

from tools import (
    TOOLS,
    TOOL_MAP
)

from context_manager import (
    ContextManager
)

from trace import (
    TraceRecorder
)

from checkpoint import (
    save_checkpoint,
    load_checkpoint,
    clear_checkpoint
)

from approval import (
    request_approval
)

from goal_state import (
    GoalManager
)

from control_plane import (
    decide_next_action,
    is_tool_allowed,
    build_control_context
)

from lease_manager import (
    LeaseManager
)

from attention_queue import (
    AttentionQueue
)

from quota_manager import (
    QuotaManager
)

from evidence_manager import (
    EvidenceStore
)

from acceptance import (
    AcceptanceGate
)
from llm_rate_limiter import (
    wait_for_llm_slot
)

# ==========================================
# Day76 修改：
#
# Modify Evidence 不再依赖 git diff
#
# get_changed_files()
# 底层使用 git status --short
#
# 可以识别：
#
# M  old_file.py
# ?? new_file.py
# D  deleted_file.py
# ==========================================

from protection import (
    get_changed_files
)


# ==========================================
# LLM
# ==========================================

llm = ChatOpenAI(

    model=
        MODEL_NAME,

    api_key=
        MOONSHOT_API_KEY,

    base_url=
        MOONSHOT_BASE_URL
)


llm_with_tools = (
    llm.bind_tools(
        TOOLS
    )
)


SYSTEM_PROMPT = """
你是一个 Coding Agent。

你工作在一个 Runtime 和 Control Plane
管理的长程 Coding Task 中。

Runtime会告诉你：

- 当前Goal
- 已完成Todo
- 当前Todo
- 当前允许使用的Tools

你必须严格围绕当前Todo工作。

不能仅通过文字声明任务完成。

真正的任务状态由Runtime根据
Tool执行结果和Evidence更新。

如果之前的Verification失败，
你应该根据测试错误继续定位和修改代码，
而不是重复相同的失败操作。
"""


# ==========================================
# LLM Retry
# ==========================================
def invoke_with_retry(
    messages: list,
    max_retries: int = 3
):

    for attempt in range(
        1,
        max_retries + 1
    ):

        try:

            # ==================================
            # Day76：
            #
            # 真正发送每一次HTTP请求之前
            # 都先经过共享Rate Limiter
            # ==================================

            wait_for_llm_slot()


            return (
                llm_with_tools.invoke(
                    messages
                )
            )


        except RateLimitError:

            if (
                attempt
                ==
                max_retries
            ):

                raise


            # ==================================
            # Rate Limiter已经负责主要节流。
            #
            # 如果仍然出现429，
            # 再额外等待一次。
            # ==================================

            wait_time = 25


            print(
                f"\n仍触发RPM限制，"
                f"额外等待{wait_time}秒..."
            )


            time.sleep(
                wait_time
            )


        except (
            APITimeoutError,
            APIConnectionError
        ):

            if (
                attempt
                ==
                max_retries
            ):

                raise


            wait_time = (
                2 ** attempt
            )


            print(
                f"\nAPI调用失败，"
                f"等待{wait_time}秒..."
            )


            time.sleep(
                wait_time
            )
# ==========================================
# Tool基础执行结果
# ==========================================

def tool_succeeded(
    tool_name: str,
    result
) -> bool:

    if not isinstance(
        result,
        dict
    ):

        return True


    # ======================================
    # Verification比较特殊
    #
    # 它关心的是测试有没有PASS
    # ======================================

    if (
        tool_name
        ==
        "verify_project"
    ):

        return bool(
            result.get(
                "passed",
                False
            )
        )


    # ======================================
    # 普通Tool：
    #
    # list_file / read_file
    # write_file / replace_text
    # git_diff
    #
    # 看它自己的 success
    # ======================================

    return bool(
        result.get(
            "success",
            False
        )
    )


# ==========================================
# 保存Runtime Checkpoint
# ==========================================

def save_runtime_checkpoint(
    user_task: str,
    next_tick: int,
    context: ContextManager,
    worker_id: str,
    quota_manager: QuotaManager
):

    return save_checkpoint(
        {

            "user_task":
                user_task,

            "next_tick":
                next_tick,

            "worker_id":
                worker_id,

            "context_state":
                context.export_state(),

            "quota_state":
                quota_manager
                .export_state()
        }
    )


# ==========================================
# Quota耗尽
# ==========================================

def block_for_quota(
    goal_manager: GoalManager,
    attention_queue: AttentionQueue,
    todo_id: str,
    quota_result: dict
):

    resource = (
        quota_result.get(
            "resource",
            "unknown"
        )
    )


    message = (
        f"Quota耗尽："
        f"{resource}"
    )


    goal_manager.block_todo(
        todo_id,
        message
    )


    attention_queue.add(

        goal_id=
            goal_manager.goal.goal_id,

        todo_id=
            todo_id,

        kind=
            "QUOTA_EXHAUSTED",

        message=
            message,

        details=
            quota_result
    )


# ==========================================
# Evidence驱动Todo状态
#
# Tool Success != Todo Success
# ==========================================

def update_todo_from_evidence(
    todo,
    tool_records: list,
    goal_manager: GoalManager,
    evidence_store: EvidenceStore,
    attention_queue: AttentionQueue
):

    goal_id = (
        goal_manager
        .goal
        .goal_id
    )


    # ==========================================
    # Inspect Evidence
    # ==========================================

    if (
        todo.todo_id
        ==
        "inspect"
    ):

        successful_reads = [

            record

            for record
            in tool_records

            if (

                record[
                    "tool_name"
                ]
                ==
                "read_file"

                and

                tool_succeeded(

                    record[
                        "tool_name"
                    ],

                    record[
                        "result"
                    ]
                )
            )
        ]


        passed = (
            len(
                successful_reads
            )
            >
            0
        )


        evidence_store.add(

            goal_id=
                goal_id,

            todo_id=
                "inspect",

            kind=
                "INSPECTION",

            passed=
                passed,

            summary=(

                (
                    f"成功读取"
                    f"{len(successful_reads)}"
                    f"个文件"
                )

                if passed

                else

                "尚未真正读取代码文件"
            ),

            data={

                "read_count":
                    len(
                        successful_reads
                    )
            }
        )


        if passed:

            goal_manager.complete_todo(

                "inspect",

                "已读取Repository代码"
            )


        else:

            goal_manager.retry_todo(

                "inspect",

                (
                    "仅浏览文件列表不足以"
                    "完成Inspect，"
                    "需要read_file。"
                )
            )


        return


    # ==========================================
    # Modify Evidence
    #
    # Day76重点修复区域
    # ==========================================

    if (
        todo.todo_id
        ==
        "modify"
    ):

        # ======================================
        # 1.
        # 本Tick中是否执行过真正的修改Tool
        # ======================================

        successful_modify = any(

            (

                record[
                    "tool_name"
                ]

                in {
                    "write_file",
                    "replace_text"
                }

                and

                tool_succeeded(

                    record[
                        "tool_name"
                    ],

                    record[
                        "result"
                    ]
                )
            )

            for record
            in tool_records
        )


        # ======================================
        # 2.
        # Runtime独立检查Workspace变化
        #
        # 这里不再使用：
        #
        # git diff
        #
        # 因为git diff默认看不到：
        #
        # ?? new_file.py
        #
        # 改成get_changed_files()
        #
        # 底层：
        #
        # git status --short
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


        # ======================================
        # 只要Git确认至少存在一个变化文件
        #
        # 就表示Workspace确实有变化
        # ======================================

        has_changes = (

            len(
                changed_files
            )
            >
            0
        )


        # ======================================
        # Modify Todo毕业条件：
        #
        # 修改Tool执行成功
        #
        # AND
        #
        # Git确认Workspace真的变化
        # ======================================

        passed = (

            successful_modify

            and

            has_changes
        )


        # ======================================
        # Evidence持久化
        # ======================================

        evidence_store.add(

            goal_id=
                goal_id,

            todo_id=
                "modify",

            kind=
                "MODIFICATION",

            passed=
                passed,

            summary=(

                "代码修改产生真实Workspace变化"

                if passed

                else

                (
                    "修改Tool没有产生"
                    "可验证的Workspace变化"
                )
            ),

            data={

                "modify_tool_success":
                    successful_modify,

                "has_changes":
                    has_changes,

                "changed_files":
                    changed_files
            }
        )


        if passed:

            goal_manager.complete_todo(

                "modify",

                (
                    "Runtime确认Workspace"
                    "存在真实文件变化"
                )
            )


        else:

            goal_manager.retry_todo(

                "modify",

                (
                    "没有产生真实Workspace变化，"
                    "Modify不能完成。"
                )
            )


        return


    # ==========================================
    # Review Evidence
    # ==========================================

    if (
        todo.todo_id
        ==
        "review"
    ):

        diff_record = None


        for record in (
            tool_records
        ):

            if (
                record[
                    "tool_name"
                ]
                ==
                "git_diff"
            ):

                diff_record = (
                    record
                )

                break


        if diff_record is None:

            has_changes = False

            diff_text = ""


        else:

            result = (
                diff_record[
                    "result"
                ]
            )


            has_changes = (

                result.get(
                    "success",
                    False
                )

                and

                bool(
                    result.get(
                        "stdout",
                        ""
                    ).strip()
                )
            )


            diff_text = (
                result.get(
                    "stdout",
                    ""
                )
            )


        evidence_store.add(

            goal_id=
                goal_id,

            todo_id=
                "review",

            kind=
                "GIT_DIFF",

            passed=
                has_changes,

            summary=(

                "Git Diff存在真实变更"

                if has_changes

                else

                "Git Diff为空"
            ),

            data={

                "has_changes":
                    has_changes,

                "diff":
                    diff_text[
                        :5000
                    ]
            }
        )


        if has_changes:

            goal_manager.complete_todo(

                "review",

                "Git Diff已审查"
            )


        else:

            goal_manager.reopen_from(

                "modify",

                (
                    "Review发现没有"
                    "实际代码Diff"
                )
            )


        return


    # ==========================================
    # Verification Evidence
    # ==========================================

    if (
        todo.todo_id
        ==
        "verify"
    ):

        verify_record = None


        for record in (
            tool_records
        ):

            if (
                record[
                    "tool_name"
                ]
                ==
                "verify_project"
            ):

                verify_record = (
                    record
                )

                break


        # ======================================
        # 根本没运行Verification
        # ======================================

        if verify_record is None:

            goal_manager.retry_todo(

                "verify",

                (
                    "没有执行"
                    "Verification"
                )
            )

            return


        result = (
            verify_record[
                "result"
            ]
        )


        passed = bool(

            result.get(
                "passed",
                False
            )
        )


        status = (
            result.get(
                "status",
                "UNKNOWN"
            )
        )


        # ======================================
        # 保存Verification Evidence
        # ======================================

        evidence_store.add(

            goal_id=
                goal_id,

            todo_id=
                "verify",

            kind=
                "VERIFICATION",

            passed=
                passed,

            summary=(

                "项目Verification通过"

                if passed

                else

                (
                    f"Verification失败："
                    f"{status}"
                )
            ),

            data={

                "status":
                    status,

                "returncode":
                    result.get(
                        "returncode"
                    ),

                "stdout":
                    result.get(
                        "stdout",
                        ""
                    )[
                        :5000
                    ],

                "stderr":
                    result.get(
                        "stderr",
                        ""
                    )[
                        :3000
                    ]
            }
        )


        # ======================================
        # PASS
        # ======================================

        if passed:

            goal_manager.complete_todo(

                "verify",

                "Verification PASS"
            )

            return


        # ======================================
        # TEST_FAILED
        #
        # 代码问题：
        #
        # 回到Modify
        # ======================================

        if (
            status
            ==
            "TEST_FAILED"
        ):

            goal_manager.reopen_from(

                "modify",

                (
                    "Verification失败，"
                    "根据测试错误重新修改。"
                )
            )

            return


        # ======================================
        # Infrastructure Error
        # ======================================

        if (
            status
            ==
            "INFRA_ERROR"
        ):

            goal_manager.block_todo(

                "verify",

                (
                    "Verification"
                    "基础设施异常"
                )
            )


            attention_queue.add(

                goal_id=
                    goal_id,

                todo_id=
                    "verify",

                kind=
                    "INFRA_ERROR",

                message=(
                    "Verification无法运行，"
                    "请检查Docker环境。"
                ),

                details=
                    result
            )

            return


        # ======================================
        # Verification Policy Denied
        # ======================================

        if (
            status
            ==
            "POLICY_DENIED"
        ):

            goal_manager.block_todo(

                "verify",

                (
                    "Verification命令"
                    "违反安全策略"
                )
            )


            attention_queue.add(

                goal_id=
                    goal_id,

                todo_id=
                    "verify",

                kind=
                    "VERIFICATION_POLICY_DENIED",

                message=(
                    "Agent尝试使用"
                    "不允许的Verification命令。"
                ),

                details=
                    result
            )

            return


        # ======================================
        # 未知Verification失败
        # ======================================

        goal_manager.retry_todo(

            "verify",

            "未知Verification失败"
        )


# ==========================================
# Control Tick
# ==========================================

def run_tick(
    tick_number: int,
    user_task: str,
    worker_id: str,
    goal_manager: GoalManager,
    lease_manager: LeaseManager,
    attention_queue: AttentionQueue,
    quota_manager: QuotaManager,
    evidence_store: EvidenceStore,
    context: ContextManager,
    trace: TraceRecorder
) -> dict:

    print(
        "\n"
        "================================"
    )


    print(
        f"Control Tick {tick_number}"
    )


    print(
        "================================"
    )


    # ======================================
    # 1. Control Plane
    # ======================================

    decision = (
        decide_next_action(
            goal_manager
        )
    )


    trace.record(

        "control_decision",

        {

            "tick":
                tick_number,

            "should_run":
                decision[
                    "should_run"
                ],

            "reason":
                decision[
                    "reason"
                ]
        }
    )


    if not decision[
        "should_run"
    ]:

        return {

            "continue":
                False,

            "reason":
                decision[
                    "reason"
                ]
        }


    todo = (
        decision[
            "todo"
        ]
    )


    allowed_tools = (
        decision[
            "allowed_tools"
        ]
    )


    print(
        "Current Todo:",
        todo.title
    )


    print(
        "Worker:",
        worker_id
    )


    print(
        "Allowed Tools:",
        allowed_tools
    )


    # ======================================
    # 2. Tick Quota
    # ======================================

    tick_quota = (
        quota_manager.try_consume(
            [
                "ticks"
            ]
        )
    )


    if not tick_quota[
        "allowed"
    ]:

        block_for_quota(

            goal_manager=
                goal_manager,

            attention_queue=
                attention_queue,

            todo_id=
                todo.todo_id,

            quota_result=
                tick_quota
        )


        save_runtime_checkpoint(

            user_task=
                user_task,

            next_tick=
                tick_number,

            context=
                context,

            worker_id=
                worker_id,

            quota_manager=
                quota_manager
        )


        return {

            "continue":
                False,

            "reason":
                "quota_exhausted"
        }


    # ======================================
    # 3. Claim / Lease
    # ======================================

    claim_result = (
        lease_manager.claim(

            todo_id=
                todo.todo_id,

            worker_id=
                worker_id
        )
    )


    trace.record(

        "lease_claim",

        {

            "tick":
                tick_number,

            "todo_id":
                todo.todo_id,

            "worker_id":
                worker_id,

            "result":
                claim_result
        }
    )


    if not claim_result[
        "claimed"
    ]:

        if (
            claim_result.get(
                "reason"
            )
            ==
            "lease_conflict"
        ):

            attention_queue.add(

                goal_id=
                    goal_manager
                    .goal
                    .goal_id,

                todo_id=
                    todo.todo_id,

                kind=
                    "LEASE_CONFLICT",

                message=(
                    "当前Todo已经被"
                    "其他Worker占用"
                ),

                details=
                    claim_result
            )


        save_runtime_checkpoint(

            user_task=
                user_task,

            next_tick=
                tick_number + 1,

            context=
                context,

            worker_id=
                worker_id,

            quota_manager=
                quota_manager
        )


        return {

            "continue":
                False,

            "reason":
                claim_result[
                    "reason"
                ]
        }


    lease_id = (
        claim_result[
            "lease_id"
        ]
    )


    attention_queue.resolve_matching(

        goal_id=
            goal_manager
            .goal
            .goal_id,

        todo_id=
            todo.todo_id,

        kind=
            "LEASE_CONFLICT"
    )


    # ======================================
    # 4. Context
    # ======================================

    control_context = (
        build_control_context(

            goal_manager=
                goal_manager,

            todo=
                todo,

            allowed_tools=
                allowed_tools
        )
    )


    messages = (
        context.build_messages()
    )


    messages.append(

        HumanMessage(

            content=
                control_context
        )
    )


    # ======================================
    # 5. LLM Quota
    # ======================================

    llm_quota = (
        quota_manager.try_consume(
            [
                "llm_calls"
            ]
        )
    )


    if not llm_quota[
        "allowed"
    ]:

        block_for_quota(

            goal_manager=
                goal_manager,

            attention_queue=
                attention_queue,

            todo_id=
                todo.todo_id,

            quota_result=
                llm_quota
        )


        save_runtime_checkpoint(

            user_task=
                user_task,

            next_tick=
                tick_number + 1,

            context=
                context,

            worker_id=
                worker_id,

            quota_manager=
                quota_manager
        )


        return {

            "continue":
                False,

            "reason":
                "quota_exhausted"
        }


    # ======================================
    # 6. LLM
    # ======================================

    response = (
        invoke_with_retry(
            messages
        )
    )


    trace.record(

        "llm_response",

        {

            "tick":
                tick_number,

            "todo_id":
                todo.todo_id,

            "worker_id":
                worker_id,

            "tool_calls": [

                {

                    "name":
                        call[
                            "name"
                        ],

                    "args":
                        call[
                            "args"
                        ],

                    "id":
                        call[
                            "id"
                        ]
                }

                for call
                in response.tool_calls
            ]
        }
    )


    # ======================================
    # 7. 没有Tool Call
    # ======================================

    if not response.tool_calls:

        context.add_step(

            ai_message=
                response,

            tool_records=[]
        )


        goal_manager.retry_todo(

            todo.todo_id,

            (
                "模型未执行Tool，"
                "Todo未被Runtime接受。"
            )
        )


        save_runtime_checkpoint(

            user_task=
                user_task,

            next_tick=
                tick_number + 1,

            context=
                context,

            worker_id=
                worker_id,

            quota_manager=
                quota_manager
        )


        return {

            "continue":
                True,

            "reason":
                "no_tool_call"
        }


    tool_records = []


    blocked = False

    lease_lost = False

    quota_blocked = False

    control_failure = False


    # ======================================
    # 8. Tool Calls
    # ======================================

    for tool_call in (
        response.tool_calls
    ):

        tool_name = (
            tool_call[
                "name"
            ]
        )


        tool_args = (
            tool_call[
                "args"
            ]
        )


        tool_call_id = (
            tool_call[
                "id"
            ]
        )


        print(
            "\nTool:",
            tool_name
        )


        # ==================================
        # 当前Tick已经不能继续执行
        # ==================================

        if (
            blocked
            or
            lease_lost
            or
            quota_blocked
        ):

            result = {

                "success":
                    False,

                "error":
                    (
                        "当前Tick已经进入"
                        "不可继续执行状态"
                    )
            }


        else:

            # ==================================
            # Lease Renew
            # ==================================

            renew_result = (
                lease_manager.renew(

                    todo_id=
                        todo.todo_id,

                    worker_id=
                        worker_id,

                    lease_id=
                        lease_id
                )
            )


            if not renew_result[
                "renewed"
            ]:

                lease_lost = (
                    True
                )


                result = {

                    "success":
                        False,

                    "error":
                        (
                            "Lease已经失效，"
                            "Runtime拒绝执行Tool。"
                        )
                }


                attention_queue.add(

                    goal_id=
                        goal_manager
                        .goal
                        .goal_id,

                    todo_id=
                        todo.todo_id,

                    kind=
                        "LEASE_LOST",

                    message=(
                        "Worker在执行Tool前"
                        "失去了Todo Lease"
                    ),

                    details={

                        "worker_id":
                            worker_id,

                        "lease_id":
                            lease_id,

                        "tool_name":
                            tool_name
                    }
                )


            # ==================================
            # Hard Tool Policy
            # ==================================

            elif not is_tool_allowed(

                todo_id=
                    todo.todo_id,

                tool_name=
                    tool_name
            ):

                control_failure = (
                    True
                )


                result = {

                    "success":
                        False,

                    "error": (

                        "Control Plane拒绝Tool。"

                        f"当前Todo="
                        f"{todo.todo_id}，"

                        f"不允许调用"
                        f"{tool_name}。"
                    )
                }


            else:

                # ==================================
                # Human Approval
                # ==================================

                approval = (
                    request_approval(

                        tool_name=
                            tool_name,

                        tool_args=
                            tool_args
                    )
                )


                trace.record(

                    "approval_decision",

                    {

                        "tick":
                            tick_number,

                        "tool_name":
                            tool_name,

                        "approved":
                            approval[
                                "approved"
                            ],

                        "reason":
                            approval[
                                "reason"
                            ]
                    }
                )


                if not approval[
                    "approved"
                ]:

                    blocked = (
                        True
                    )


                    result = {

                        "success":
                            False,

                        "error":
                            (
                                "Human Gate"
                                "拒绝执行"
                            ),

                        "approval":
                            approval[
                                "reason"
                            ]
                    }


                    goal_manager.block_todo(

                        todo.todo_id,

                        (
                            "Human Gate"
                            "拒绝Tool"
                        )
                    )


                    attention_queue.add(

                        goal_id=
                            goal_manager
                            .goal
                            .goal_id,

                        todo_id=
                            todo.todo_id,

                        kind=
                            (
                                "HUMAN_"
                                "APPROVAL_DENIED"
                            ),

                        message=(
                            f"用户拒绝Tool："
                            f"{tool_name}"
                        ),

                        details={

                            "tool_name":
                                tool_name,

                            "tool_args":
                                tool_args
                        }
                    )


                else:

                    # ==================================
                    # Tool Quota
                    # ==================================

                    quota_resources = [
                        "tool_calls"
                    ]


                    if (
                        tool_name
                        ==
                        "verify_project"
                    ):

                        quota_resources.append(
                            "verify_calls"
                        )


                    tool_quota = (
                        quota_manager
                        .try_consume(
                            quota_resources
                        )
                    )


                    if not tool_quota[
                        "allowed"
                    ]:

                        quota_blocked = (
                            True
                        )


                        block_for_quota(

                            goal_manager=
                                goal_manager,

                            attention_queue=
                                attention_queue,

                            todo_id=
                                todo.todo_id,

                            quota_result=
                                tool_quota
                        )


                        result = {

                            "success":
                                False,

                            "error":
                                (
                                    "Quota耗尽，"
                                    "Runtime拒绝执行Tool。"
                                ),

                            "quota":
                                tool_quota
                        }


                    else:

                        # ==============================
                        # 真正执行Tool
                        # ==============================

                        tool = (
                            TOOL_MAP.get(
                                tool_name
                            )
                        )


                        if tool is None:

                            control_failure = (
                                True
                            )


                            result = {

                                "success":
                                    False,

                                "error":
                                    (
                                        f"未知Tool："
                                        f"{tool_name}"
                                    )
                            }


                        else:

                            try:

                                result = (
                                    tool.invoke(
                                        tool_args
                                    )
                                )


                            except Exception as e:

                                result = {

                                    "success":
                                        False,

                                    "error":
                                        str(e)
                                }


        print(
            "Result:",
            result
        )


        trace.record(

            "tool_result",

            {

                "tick":
                    tick_number,

                "todo_id":
                    todo.todo_id,

                "tool_name":
                    tool_name,

                "result":
                    str(
                        result
                    )[
                        :2000
                    ]
            }
        )


        tool_message = ToolMessage(

            content=
                str(
                    result
                ),

            tool_call_id=
                tool_call_id
        )


        tool_records.append(
            {

                "tool_name":
                    tool_name,

                "tool_args":
                    tool_args,

                "result":
                    result,

                "tool_message":
                    tool_message
            }
        )


    # ======================================
    # 9. Context保存完整Agent Step
    # ======================================

    context.add_step(

        ai_message=
            response,

        tool_records=
            tool_records
    )


    # ======================================
    # 10.
    # Evidence驱动Todo State
    # ======================================

    if (
        blocked
        or
        quota_blocked
    ):

        pass


    elif lease_lost:

        # ==================================
        # Worker失去Lease以后
        #
        # 不能再修改Todo State
        # ==================================

        pass


    elif control_failure:

        goal_manager.retry_todo(

            todo.todo_id,

            (
                "存在被Control Plane"
                "拒绝或未知的Tool调用"
            )
        )


    else:

        update_todo_from_evidence(

            todo=
                todo,

            tool_records=
                tool_records,

            goal_manager=
                goal_manager,

            evidence_store=
                evidence_store,

            attention_queue=
                attention_queue
        )


    # ======================================
    # 11. Checkpoint
    # ======================================

    save_runtime_checkpoint(

        user_task=
            user_task,

        next_tick=
            tick_number + 1,

        context=
            context,

        worker_id=
            worker_id,

        quota_manager=
            quota_manager
    )


    print(
        "\nGoal State:"
    )


    print(
        goal_manager.render()
    )


    print(
        "\nQuota State:"
    )


    print(
        quota_manager.render()
    )


    print(
        "\nEvidence:"
    )


    print(
        evidence_store.render(
            goal_manager
            .goal
            .goal_id
        )
    )


    print(
        "\nAttention Queue:"
    )


    print(
        attention_queue.render_open(
            goal_manager
            .goal
            .goal_id
        )
    )


    goal_blocked = (

        goal_manager.goal.status
        ==
        "BLOCKED"
    )


    return {

        "continue":
            not (
                blocked
                or
                lease_lost
                or
                quota_blocked
                or
                goal_blocked
            ),

        "reason": (

            "blocked"

            if (
                blocked
                or
                goal_blocked
            )

            else

            "lease_lost"

            if lease_lost

            else

            "quota_exhausted"

            if quota_blocked

            else

            "tick_complete"
        )
    }


# ==========================================
# Acceptance
# ==========================================

def try_accept_goal(
    goal_manager: GoalManager,
    evidence_store: EvidenceStore,
    attention_queue: AttentionQueue,
    acceptance_gate: AcceptanceGate
) -> dict:

    gate_result = (
        acceptance_gate.evaluate(
            goal_manager
        )
    )


    if gate_result[
        "accepted"
    ]:

        writeback_result = (
            acceptance_gate.writeback(

                goal_manager=
                    goal_manager,

                gate_result=
                    gate_result
            )
        )


        return {

            "accepted":
                True,

            "gate_result":
                gate_result,

            "writeback":
                writeback_result
        }


    # ======================================
    # Todo全部DONE但Evidence不够
    #
    # 属于Runtime状态不一致
    # ======================================

    goal_manager.block_todo(

        "verify",

        (
            "Todos全部完成，"
            "但Evidence Gate拒绝验收"
        )
    )


    attention_queue.add(

        goal_id=
            goal_manager
            .goal
            .goal_id,

        todo_id=
            "verify",

        kind=
            "ACCEPTANCE_REJECTED",

        message=(
            "所有Todo完成，"
            "但客观Evidence不足。"
        ),

        details=
            gate_result
    )


    return {

        "accepted":
            False,

        "gate_result":
            gate_result,

        "writeback":
            None
    }


# ==========================================
# Agent Runtime
# ==========================================

def run_agent(
    user_task: str,

    max_ticks: int = 12,

    max_steps: int | None = None,

    max_llm_calls: int = 8,

    max_tool_calls: int = 20,

    max_verify_calls: int = 4,

    max_runtime_seconds: float = 300
) -> str:

    # ======================================
    # 兼容旧Eval Runner
    # ======================================

    if max_steps is not None:

        max_ticks = (
            max_steps
        )


    # ======================================
    # Goal
    # ======================================

    goal_manager = (
        GoalManager()
    )


    goal_manager.get_or_create_goal(
        user_task
    )


    # ======================================
    # Context
    # ======================================

    context = ContextManager(

        system_prompt=
            SYSTEM_PROMPT,

        user_goal=
            user_task,

        max_recent_steps=4,

        max_history_items=20,

        max_result_chars=800
    )


    # ======================================
    # Trace
    # ======================================

    trace = (
        TraceRecorder(
            "agent_task"
        )
    )


    # ======================================
    # Attention
    # ======================================

    attention_queue = (
        AttentionQueue()
    )


    # ======================================
    # Evidence
    # ======================================

    evidence_store = (
        EvidenceStore()
    )


    # ======================================
    # Acceptance Gate
    # ======================================

    acceptance_gate = (
        AcceptanceGate(

            evidence_store=
                evidence_store,

            attention_queue=
                attention_queue
        )
    )


    # ======================================
    # Quota
    # ======================================

    quota_manager = QuotaManager(

        max_ticks=
            max_ticks,

        max_llm_calls=
            max_llm_calls,

        max_tool_calls=
            max_tool_calls,

        max_verify_calls=
            max_verify_calls,

        max_runtime_seconds=
            max_runtime_seconds
    )


    # ======================================
    # Resume
    # ======================================

    checkpoint = (
        load_checkpoint()
    )


    tick_number = 1


    worker_id = (

        "worker_"
        +
        uuid4()
        .hex[:8]
    )


    if (

        checkpoint

        and

        checkpoint.get(
            "user_task"
        )

        ==

        user_task
    ):

        context.import_state(

            checkpoint[
                "context_state"
            ]
        )


        tick_number = (
            checkpoint.get(
                "next_tick",
                1
            )
        )


        worker_id = (
            checkpoint.get(
                "worker_id",
                worker_id
            )
        )


        quota_state = (
            checkpoint.get(
                "quota_state"
            )
        )


        if quota_state:

            quota_manager.import_state(
                quota_state
            )


        print(
            "\n发现Checkpoint，"
            f"从Control Tick "
            f"{tick_number}继续。"
        )


    print(
        "Worker ID:",
        worker_id
    )


    # ======================================
    # Lease Manager
    # ======================================

    lease_manager = LeaseManager(

        goal_manager=
            goal_manager,

        lease_seconds=300
    )


    # ======================================
    # Core Tick Loop
    # ======================================

    while True:

        goal_manager.load()


        decision = (
            decide_next_action(
                goal_manager
            )
        )


        if not decision[
            "should_run"
        ]:

            break


        tick_result = (
            run_tick(

                tick_number=
                    tick_number,

                user_task=
                    user_task,

                worker_id=
                    worker_id,

                goal_manager=
                    goal_manager,

                lease_manager=
                    lease_manager,

                attention_queue=
                    attention_queue,

                quota_manager=
                    quota_manager,

                evidence_store=
                    evidence_store,

                context=
                    context,

                trace=
                    trace
            )
        )


        if not tick_result[
            "continue"
        ]:

            break


        # ==================================
        # Todo全DONE
        #
        # 只是申请Acceptance
        # ==================================

        if (
            goal_manager
            .all_todos_done()
        ):

            acceptance_result = (
                try_accept_goal(

                    goal_manager=
                        goal_manager,

                    evidence_store=
                        evidence_store,

                    attention_queue=
                        attention_queue,

                    acceptance_gate=
                        acceptance_gate
                )
            )


            if acceptance_result[
                "accepted"
            ]:

                clear_checkpoint()


                return (

                    "Goal已通过Evidence Gate。"
                    "\n\n"

                    +
                    goal_manager.render()

                    +
                    "\n\nEvidence:\n"

                    +
                    evidence_store.render(
                        goal_manager
                        .goal
                        .goal_id
                    )

                    +
                    "\n\nAccepted Writeback:\n"

                    +
                    str(
                        acceptance_result[
                            "writeback"
                        ]
                    )
                )


            break


        tick_number += 1


    # ======================================
    # Final State
    # ======================================

    goal_manager.load()


    # ======================================
    # 极端情况下：
    #
    # Loop结束时Todo刚好全部DONE
    # ======================================

    if (
        goal_manager
        .all_todos_done()
    ):

        acceptance_result = (
            try_accept_goal(

                goal_manager=
                    goal_manager,

                evidence_store=
                    evidence_store,

                attention_queue=
                    attention_queue,

                acceptance_gate=
                    acceptance_gate
            )
        )


        if acceptance_result[
            "accepted"
        ]:

            clear_checkpoint()


            return (

                "Goal已通过Evidence Gate。"
                "\n\n"

                +
                goal_manager.render()

                +
                "\n\nEvidence:\n"

                +
                evidence_store.render(
                    goal_manager
                    .goal
                    .goal_id
                )
            )


    # ======================================
    # BLOCKED
    # ======================================

    if (

        goal_manager.goal

        and

        goal_manager.goal.status
        ==
        "BLOCKED"
    ):

        return (

            "Goal当前处于BLOCKED状态。"
            "\n\n"

            +
            goal_manager.render()

            +
            "\n\nQuota:\n"

            +
            quota_manager.render()

            +
            "\n\nEvidence:\n"

            +
            evidence_store.render(
                goal_manager
                .goal
                .goal_id
            )

            +
            "\n\nAttention Queue:\n"

            +
            attention_queue.render_open(
                goal_manager
                .goal
                .goal_id
            )
        )


    # ======================================
    # 其它停止状态
    # ======================================

    return (

        "Agent停止运行，"
        "Goal仍未完成。"
        "\n\n"

        +
        goal_manager.render()

        +
        "\n\nQuota:\n"

        +
        quota_manager.render()

        +
        "\n\nEvidence:\n"

        +
        evidence_store.render(
            goal_manager
            .goal
            .goal_id
        )

        +
        "\n\nAttention Queue:\n"

        +
        attention_queue.render_open(
            goal_manager
            .goal
            .goal_id
        )
    )
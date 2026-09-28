import json
import time

from langchain_openai import (
    ChatOpenAI
)

from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    ToolMessage
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

from llm_rate_limiter import (
    wait_for_llm_slot
)


# ==========================================
# Bare Agent使用与LoopCoder完全相同的模型
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

你可以使用提供的工具：

- 浏览文件
- 读取文件
- 修改文件
- 查看Git Diff
- 在Docker Sandbox中运行pytest

你的目标是完成用户给出的代码任务。

工作建议：

1. 先检查Repository和相关代码。
2. 根据任务修改代码。
3. 使用测试验证结果。
4. 如果测试失败，根据错误继续修复。
5. 不要修改用户明确禁止修改的文件。
6. 不要仅通过文字声称完成。
7. 在正式完成前，应使用verify_project并确保测试通过。
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
            # Bare和LoopCoder共用同一个
            # Rate Limiter。
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


            wait_time = 25


            print(
                f"\n[Bare] 仍触发RPM限制，"
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
                f"\n[Bare] API异常，"
                f"等待{wait_time}秒..."
            )


            time.sleep(
                wait_time
            )


# ==========================================
# Bare Agent Loop
# ==========================================

def run_bare_agent(
    user_task: str,
    max_steps: int = 16
) -> dict:

    messages = [

        SystemMessage(
            content=
                SYSTEM_PROMPT
        ),

        HumanMessage(
            content=
                user_task
        )
    ]


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


    verified = False

    final_text = ""

    agent_error = None


    for step in range(
        1,
        max_steps + 1
    ):

        # ======================================
        # Step开始
        # ======================================

        metrics[
            "steps"
        ] += 1


        print(
            "\n"
            "================================"
        )


        print(
            f"Bare Agent Step {step}"
        )


        print(
            "================================"
        )


        # ======================================
        # LLM
        #
        # 这里自己捕获异常，
        # 确保之前的Metrics不会丢
        # ======================================

        try:

            metrics[
                "llm_calls"
            ] += 1


            response = (
                invoke_with_retry(
                    messages
                )
            )


        except Exception as e:

            agent_error = (

                f"{type(e).__name__}: "
                f"{e}"
            )


            print(
                "\n[Bare] Agent停止："
            )


            print(
                agent_error
            )


            break


        messages.append(
            response
        )


        # ======================================
        # 模型没有Tool Call
        # ======================================

        if not response.tool_calls:

            final_text = (
                response.content
                or
                ""
            )


            print(
                "\n[Bare] 模型停止调用Tool。"
            )


            break


        # ======================================
        # Tools
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


            metrics[
                "tool_calls"
            ] += 1


            print(
                "\n[Bare] Tool:",
                tool_name
            )


            tool = (
                TOOL_MAP.get(
                    tool_name
                )
            )


            if tool is None:

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
                "[Bare] Result:",
                result
            )


            # ==================================
            # Verification Metrics
            # ==================================

            if (
                tool_name
                ==
                "verify_project"
            ):

                metrics[
                    "verify_calls"
                ] += 1


                if (
                    isinstance(
                        result,
                        dict
                    )

                    and

                    result.get(
                        "passed",
                        False
                    )
                ):

                    verified = (
                        True
                    )


                else:

                    metrics[
                        "verify_failures"
                    ] += 1


            tool_message = ToolMessage(

                content=
                    json.dumps(
                        result,
                        ensure_ascii=False,
                        default=str
                    ),

                tool_call_id=
                    tool_call_id
            )


            messages.append(
                tool_message
            )


        # ======================================
        # Bare的唯一硬完成条件
        # ======================================

        if verified:

            break


    return {

        "verified":
            verified,

        "final_text":
            final_text,

        "agent_error":
            agent_error,

        "metrics":
            metrics
    }
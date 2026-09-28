import json
import os


# ==========================================
# 不同Tool的权限等级
# ==========================================

SAFE_TOOLS = {
    "list_files",
    "read_file",
    "git_diff",
    "verify_project"
}


REQUIRE_APPROVAL_TOOLS = {
    "write_file",
    "replace_text"
}


def get_permission_level(
    tool_name: str
) -> str:

    """
    判断一个Tool属于什么权限等级。

    返回：

    SAFE
    REQUIRE_APPROVAL
    UNKNOWN
    """

    if tool_name in SAFE_TOOLS:

        return "SAFE"


    if tool_name in REQUIRE_APPROVAL_TOOLS:

        return "REQUIRE_APPROVAL"


    return "UNKNOWN"


def request_approval(
    tool_name: str,
    tool_args: dict
) -> dict:

    """
    请求用户审批Tool调用。

    返回：

    {
        "approved": True/False,
        "reason": "..."
    }
    """

    permission_level = (
        get_permission_level(
            tool_name
        )
    )


    # ======================================
    # 安全Tool
    # 自动放行
    # ======================================

    if permission_level == "SAFE":

        return {
            "approved": True,
            "reason":
                "safe_tool"
        }


    # ======================================
    # 未知Tool
    # 默认拒绝
    # ======================================

    if permission_level == "UNKNOWN":

        return {
            "approved": False,
            "reason":
                "unknown_tool"
        }

    approval_mode = (
        os.getenv(
            "AGENT_APPROVAL_MODE",
            "manual"
        )
        .strip()
        .lower()
    )

    if approval_mode == "auto":

        print(
            "\n[Eval Mode]"
            f"自动批准Tool:{tool_name}"
        )

        return {
            "approved":True,
            "reason":"auto_approved_for_eval"
        }

    

    # ======================================
    # 高风险Tool
    # 请求人工批准
    # ======================================

    print(
        "\n"
        "================================"
    )

    print(
        "需要人工审批"
    )

    print(
        "================================"
    )

    print(
        "Tool:",
        tool_name
    )


    print(
        "\nArguments:"
    )


    print(
        json.dumps(
            tool_args,
            ensure_ascii=False,
            indent=2
        )
    )


    print(
        "\n该操作会修改工作区文件。"
    )


    while True:

        answer = input(
            "\n允许执行？ [y/n]: "
        ).strip().lower()


        if answer in {
            "y",
            "yes"
        }:

            return {
                "approved": True,
                "reason":
                    "approved_by_user"
            }


        if answer in {
            "n",
            "no"
        }:

            return {
                "approved": False,
                "reason":
                    "denied_by_user"
            }


        print(
            "请输入 y 或 n。"
        )
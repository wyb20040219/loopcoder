from goal_state import (
    GoalManager,
    TodoItem
)


# ==========================================
# 每个Todo允许哪些Tool
# ==========================================

TODO_ALLOWED_TOOLS = {

    "inspect": {
        "list_files",
        "read_file"
    },

    # ======================================
    # Day73：
    #
    # 修改阶段仍然允许继续Inspect
    #
    # 因为真实Coding任务不可能：
    # “看完一次以后永远不能再看”
    # ======================================

    "modify": {
        "list_files",
        "read_file",
        "write_file",
        "replace_text"
    },

    "review": {
        "git_diff"
    },

    "verify": {
        "verify_project"
    }
}


# ==========================================
# Control Decision
# ==========================================

def decide_next_action(
    goal_manager: GoalManager
) -> dict:

    goal = (
        goal_manager.goal
    )


    # ======================================
    # 没有Goal
    # ======================================

    if goal is None:

        return {
            "should_run": False,
            "reason": "no_goal",
            "todo": None,
            "allowed_tools": []
        }


    # ======================================
    # Goal已经结束
    # ======================================

    if goal.status in {
        "DONE",
        "FAILED"
    }:

        return {

            "should_run": False,

            "reason":
                f"goal_{goal.status.lower()}",

            "todo":
                None,

            "allowed_tools":
                []
        }


    # ======================================
    # Goal被BLOCK
    # ======================================

    if (
        goal.status
        ==
        "BLOCKED"
    ):

        return {
            "should_run": False,
            "reason": "goal_blocked",
            "todo": None,
            "allowed_tools": []
        }


    # ======================================
    # 找下一Todo
    # ======================================

    todo = (
        goal_manager
        .get_next_todo()
    )


    if todo is None:

        return {
            "should_run": False,
            "reason": "no_remaining_todo",
            "todo": None,
            "allowed_tools": []
        }


    allowed_tools = list(

        TODO_ALLOWED_TOOLS.get(
            todo.todo_id,
            set()
        )
    )


    return {

        "should_run":
            True,

        "reason":
            "todo_available",

        "todo":
            todo,

        "allowed_tools":
            allowed_tools
    }


# ==========================================
# Hard Tool Permission
# ==========================================

def is_tool_allowed(
    todo_id: str,
    tool_name: str
) -> bool:

    allowed_tools = (
        TODO_ALLOWED_TOOLS.get(
            todo_id,
            set()
        )
    )


    return (
        tool_name
        in
        allowed_tools
    )


# ==========================================
# 给LLM的Control Context
# ==========================================

def build_control_context(
    goal_manager: GoalManager,
    todo: TodoItem,
    allowed_tools: list[str]
) -> str:

    goal = (
        goal_manager.goal
    )


    if goal is None:

        return ""


    completed = [

        item.title

        for item
        in goal.todos

        if (
            item.status
            ==
            "DONE"
        )
    ]


    remaining = [

        item.title

        for item
        in goal.todos

        if (
            item.status
            in {
                "TODO",
                "RUNNING"
            }
        )
    ]


    completed_text = (

        "\n".join(

            f"- {item}"

            for item
            in completed
        )

        or

        "- 暂无"
    )


    remaining_text = (

        "\n".join(

            f"- {item}"

            for item
            in remaining
        )

        or

        "- 暂无"
    )


    allowed_text = (

        ", ".join(
            allowed_tools
        )

        or

        "无"
    )


    return f"""
==============================
Control Plane State
==============================

Goal：
{goal.objective}

Goal Status：
{goal.status}

已经完成：
{completed_text}

当前Todo：
{todo.title}

尚未完成：
{remaining_text}

当前Todo允许使用的工具：
{allowed_text}

要求：

1. 只围绕当前Todo工作。
2. 不要重复已经完成且无需重新处理的Todo。
3. 只能调用当前Todo允许的工具。
4. 如果Tool执行失败，根据Tool结果继续处理。
5. 不允许仅通过文字声称Todo已完成。
6. Verification失败后，Runtime可能重新打开Modify阶段。
7. 修改阶段应根据之前的测试错误继续修复，而不是重复同一个失败操作。
"""
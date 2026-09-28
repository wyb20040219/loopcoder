from goal_state import (
    GoalManager
)

from control_plane import (
    decide_next_action,
    build_control_context,
    is_tool_allowed
)


manager = (
    GoalManager()
)


manager.create_goal(
    "修复测试项目"
)


# ==========================================
# 第一次决策
# ==========================================

decision = (
    decide_next_action(
        manager
    )
)


print(
    "\n第一次Control Decision："
)

print(
    "Todo:",
    decision[
        "todo"
    ].title
)

print(
    "Allowed Tools:",
    decision[
        "allowed_tools"
    ]
)


print(
    build_control_context(

        manager,

        decision[
            "todo"
        ],

        decision[
            "allowed_tools"
        ]
    )
)


# ==========================================
# 模拟Inspect完成
# ==========================================

manager.start_todo(
    "inspect"
)


manager.complete_todo(
    "inspect"
)


# ==========================================
# 第二次决策
# ==========================================

decision = (
    decide_next_action(
        manager
    )
)


print(
    "\n第二次Control Decision："
)

print(
    "Todo:",
    decision[
        "todo"
    ].title
)

print(
    "Allowed Tools:",
    decision[
        "allowed_tools"
    ]
)


# ==========================================
# 测试Tool Permission
# ==========================================

print(
    "\nModify阶段调用replace_text：",
    is_tool_allowed(
        "modify",
        "replace_text"
    )
)


print(
    "Review阶段调用replace_text：",
    is_tool_allowed(
        "review",
        "replace_text"
    )
)
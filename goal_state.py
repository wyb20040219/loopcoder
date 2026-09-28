import json

from datetime import datetime
from pathlib import Path
from typing import Literal
from uuid import uuid4

from pydantic import (
    BaseModel
)


BASE_DIR = Path(
    __file__
).resolve().parent


GOAL_DIR = (
    BASE_DIR
    / "goals"
)


GOAL_DIR.mkdir(
    exist_ok=True
)


ACTIVE_GOAL_PATH = (
    GOAL_DIR
    / "active_goal.json"
)


TodoStatus = Literal[
    "TODO",
    "RUNNING",
    "BLOCKED",
    "DONE"
]


GoalStatus = Literal[
    "RUNNING",
    "BLOCKED",
    "DONE",
    "FAILED"
]


class TodoItem(
    BaseModel
):

    todo_id: str

    title: str

    status: TodoStatus = (
        "TODO"
    )

    last_message: str = (
        ""
    )

    # ======================================
    # Day71 Claim / Lease
    # ======================================

    claimed_by: str | None = None

    lease_id: str | None = None

    lease_expires_at: str | None = None


class GoalState(
    BaseModel
):

    goal_id: str

    objective: str

    status: GoalStatus = (
        "RUNNING"
    )

    acceptance_criteria: list[str]

    todos: list[TodoItem]

    current_todo_id: (
        str
        | None
    ) = None

    # ======================================
    # Day73
    # ======================================

    accepted: bool = False

    accepted_at: (
        str
        | None
    ) = None

    acceptance_summary: (
        dict
        | None
    ) = None

    created_at: str

    updated_at: str


class GoalManager:

    def __init__(
        self
    ):

        self.goal: (
            GoalState
            | None
        ) = None


    def _now(
        self
    ) -> str:

        return (
            datetime.now()
            .isoformat(
                timespec="seconds"
            )
        )


    # ==========================================
    # 创建Goal
    # ==========================================

    def create_goal(
        self,
        objective: str
    ) -> GoalState:

        now = (
            self._now()
        )


        self.goal = GoalState(

            goal_id=(
                uuid4()
                .hex[:8]
            ),

            objective=
                objective,

            status=
                "RUNNING",

            acceptance_criteria=[

                (
                    "完成用户要求的代码修改"
                ),

                (
                    "使用Git Diff审查修改"
                ),

                (
                    "项目Verification通过"
                )
            ],

            todos=[

                TodoItem(
                    todo_id="inspect",
                    title="Inspect Repository"
                ),

                TodoItem(
                    todo_id="modify",
                    title="Modify Code"
                ),

                TodoItem(
                    todo_id="review",
                    title="Review Git Diff"
                ),

                TodoItem(
                    todo_id="verify",
                    title="Verify Project"
                )
            ],

            current_todo_id=
                None,

            accepted=
                False,

            accepted_at=
                None,

            acceptance_summary=
                None,

            created_at=
                now,

            updated_at=
                now
        )


        self.save()


        return self.goal


    # ==========================================
    # 保存Goal
    # ==========================================

    def save(
        self
    ):

        if self.goal is None:

            return


        self.goal.updated_at = (
            self._now()
        )


        ACTIVE_GOAL_PATH.write_text(

            json.dumps(
                self.goal.model_dump(),
                ensure_ascii=False,
                indent=2
            ),

            encoding="utf-8"
        )


    # ==========================================
    # 加载Goal
    # ==========================================

    def load(
        self
    ) -> GoalState | None:

        if not (
            ACTIVE_GOAL_PATH.exists()
        ):

            return None


        try:

            data = json.loads(

                ACTIVE_GOAL_PATH.read_text(
                    encoding="utf-8"
                )
            )


            self.goal = (
                GoalState.model_validate(
                    data
                )
            )


            return self.goal


        except Exception as e:

            print(
                "读取Goal失败：",
                e
            )


            return None


    # ==========================================
    # 获取旧Goal或创建新Goal
    # ==========================================

    def get_or_create_goal(
        self,
        objective: str
    ) -> GoalState:

        old_goal = (
            self.load()
        )


        if (
            old_goal
            and
            old_goal.objective
            ==
            objective
            and
            old_goal.status
            !=
            "DONE"
        ):

            return old_goal


        return (
            self.create_goal(
                objective
            )
        )


    # ==========================================
    # 找Todo
    # ==========================================

    def get_todo(
        self,
        todo_id: str
    ) -> TodoItem | None:

        if self.goal is None:

            return None


        for todo in (
            self.goal.todos
        ):

            if (
                todo.todo_id
                ==
                todo_id
            ):

                return todo


        return None


    # ==========================================
    # 下一Todo
    # ==========================================

    def get_next_todo(
        self
    ) -> TodoItem | None:

        if self.goal is None:

            return None


        # ======================================
        # 当前已有RUNNING Todo
        # ======================================

        if (
            self.goal.current_todo_id
        ):

            current = (
                self.get_todo(
                    self.goal.current_todo_id
                )
            )


            if (
                current
                and
                current.status
                ==
                "RUNNING"
            ):

                return current


        # ======================================
        # 其它RUNNING
        # ======================================

        for todo in (
            self.goal.todos
        ):

            if (
                todo.status
                ==
                "RUNNING"
            ):

                return todo


        # ======================================
        # 第一个TODO
        # ======================================

        for todo in (
            self.goal.todos
        ):

            if (
                todo.status
                ==
                "TODO"
            ):

                return todo


        return None


    # ==========================================
    # 启动Todo
    # ==========================================

    def start_todo(
        self,
        todo_id: str
    ):

        todo = (
            self.get_todo(
                todo_id
            )
        )


        if todo is None:

            return


        if (
            todo.status
            ==
            "DONE"
        ):

            return


        todo.status = (
            "RUNNING"
        )


        if self.goal:

            self.goal.current_todo_id = (
                todo_id
            )


        self.save()


    # ==========================================
    # 完成Todo
    # ==========================================

    def complete_todo(
        self,
        todo_id: str,
        message: str = ""
    ):

        todo = (
            self.get_todo(
                todo_id
            )
        )


        if todo is None:

            return


        todo.status = (
            "DONE"
        )


        todo.last_message = (
            message
        )


        self._clear_todo_claim(
            todo
        )


        if (
            self.goal
            and
            self.goal.current_todo_id
            ==
            todo_id
        ):

            self.goal.current_todo_id = (
                None
            )


        self.save()


    # ==========================================
    # Todo失败后普通Retry
    # ==========================================

    def retry_todo(
        self,
        todo_id: str,
        message: str = ""
    ):

        todo = (
            self.get_todo(
                todo_id
            )
        )


        if todo is None:

            return


        todo.status = (
            "TODO"
        )


        todo.last_message = (
            message
        )


        self._clear_todo_claim(
            todo
        )


        if (
            self.goal
            and
            self.goal.current_todo_id
            ==
            todo_id
        ):

            self.goal.current_todo_id = (
                None
            )


        self.save()


    # ==========================================
    # Block Todo
    # ==========================================

    def block_todo(
        self,
        todo_id: str,
        message: str = ""
    ):

        todo = (
            self.get_todo(
                todo_id
            )
        )


        if todo is None:

            return


        todo.status = (
            "BLOCKED"
        )


        todo.last_message = (
            message
        )


        self._clear_todo_claim(
            todo
        )


        if self.goal:

            self.goal.status = (
                "BLOCKED"
            )


            self.goal.current_todo_id = (
                None
            )


        self.save()


    # ==========================================
    # 人工处理问题后解除BLOCK
    # ==========================================

    def unblock_todo(
        self,
        todo_id: str,
        message: str = ""
    ):

        todo = (
            self.get_todo(
                todo_id
            )
        )


        if todo is None:

            return


        if (
            todo.status
            !=
            "BLOCKED"
        ):

            return


        todo.status = (
            "TODO"
        )


        todo.last_message = (
            message
        )


        self._clear_todo_claim(
            todo
        )


        if self.goal:

            self.goal.status = (
                "RUNNING"
            )


            self.goal.current_todo_id = (
                None
            )


        self.save()


    # ==========================================
    # Day73核心：
    #
    # 从某个Todo开始重新打开后续流程
    #
    # 例如Verify失败：
    #
    # Inspect DONE
    # Modify DONE
    # Review DONE
    # Verify FAIL
    #
    # reopen_from("modify")
    #
    # →
    #
    # Inspect DONE
    # Modify TODO
    # Review TODO
    # Verify TODO
    # ==========================================

    def reopen_from(
        self,
        todo_id: str,
        message: str = ""
    ):

        if self.goal is None:

            return


        start_index = None


        for index, todo in enumerate(
            self.goal.todos
        ):

            if (
                todo.todo_id
                ==
                todo_id
            ):

                start_index = (
                    index
                )

                break


        if start_index is None:

            return


        for index in range(
            start_index,
            len(
                self.goal.todos
            )
        ):

            todo = (
                self.goal.todos[
                    index
                ]
            )


            todo.status = (
                "TODO"
            )


            self._clear_todo_claim(
                todo
            )


            if (
                index
                ==
                start_index
            ):

                todo.last_message = (
                    message
                )


            else:

                todo.last_message = (
                    ""
                )


        self.goal.status = (
            "RUNNING"
        )


        self.goal.current_todo_id = (
            None
        )


        self.goal.accepted = (
            False
        )


        self.goal.accepted_at = (
            None
        )


        self.goal.acceptance_summary = (
            None
        )


        self.save()


    # ==========================================
    # 清理Claim / Lease
    # ==========================================

    def _clear_todo_claim(
        self,
        todo: TodoItem
    ):

        todo.claimed_by = (
            None
        )

        todo.lease_id = (
            None
        )

        todo.lease_expires_at = (
            None
        )


    # ==========================================
    # 所有Todo是否DONE
    # ==========================================

    def all_todos_done(
        self
    ) -> bool:

        if self.goal is None:

            return False


        return all(

            todo.status
            ==
            "DONE"

            for todo
            in self.goal.todos
        )


    # ==========================================
    # Day73：
    #
    # 只有Acceptance Gate通过
    # 才允许调用
    # ==========================================

    def mark_goal_accepted(
        self,
        summary: dict
    ):

        if self.goal is None:

            return


        self.goal.status = (
            "DONE"
        )


        self.goal.accepted = (
            True
        )


        self.goal.accepted_at = (
            self._now()
        )


        self.goal.acceptance_summary = (
            summary
        )


        self.goal.current_todo_id = (
            None
        )


        self.save()


    # ==========================================
    # 展示Goal
    # ==========================================

    def render(
        self
    ) -> str:

        if self.goal is None:

            return (
                "当前没有Goal"
            )


        lines = [

            (
                f"Goal ID: "
                f"{self.goal.goal_id}"
            ),

            (
                f"Objective: "
                f"{self.goal.objective}"
            ),

            (
                f"Status: "
                f"{self.goal.status}"
            ),

            (
                f"Accepted: "
                f"{self.goal.accepted}"
            ),

            ""
        ]


        for todo in (
            self.goal.todos
        ):

            if (
                todo.status
                ==
                "DONE"
            ):

                icon = "[✓]"


            elif (
                todo.status
                ==
                "RUNNING"
            ):

                icon = "[>]"


            elif (
                todo.status
                ==
                "BLOCKED"
            ):

                icon = "[!]"


            else:

                icon = "[ ]"


            line = (

                f"{icon} "
                f"{todo.title} "
                f"({todo.status})"
            )


            if todo.claimed_by:

                line += (
                    f" | owner="
                    f"{todo.claimed_by}"
                )


            if todo.lease_expires_at:

                line += (
                    f" | lease_until="
                    f"{todo.lease_expires_at}"
                )


            lines.append(
                line
            )


        return "\n".join(
            lines
        )
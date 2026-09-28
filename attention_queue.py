import json

from datetime import (
    datetime
)

from pathlib import (
    Path
)

from uuid import (
    uuid4
)

from pydantic import (
    BaseModel
)


BASE_DIR = Path(
    __file__
).resolve().parent


ATTENTION_DIR = (
    BASE_DIR
    / "attention"
)


ATTENTION_DIR.mkdir(
    exist_ok=True
)


ATTENTION_PATH = (
    ATTENTION_DIR
    / "queue.json"
)


class AttentionItem(
    BaseModel
):

    attention_id: str

    goal_id: str

    todo_id: str | None = None

    kind: str

    message: str

    details: dict = {}

    status: str = "OPEN"

    created_at: str

    resolved_at: str | None = None


class AttentionQueue:

    def _now(
        self
    ) -> str:

        return (
            datetime.now()
            .isoformat(
                timespec="seconds"
            )
        )


    def _load(
        self
    ) -> list[AttentionItem]:

        if not ATTENTION_PATH.exists():

            return []


        try:

            data = json.loads(
                ATTENTION_PATH.read_text(
                    encoding="utf-8"
                )
            )


            return [
                AttentionItem.model_validate(
                    item
                )

                for item
                in data
            ]


        except Exception:

            return []


    def _save(
        self,
        items: list[AttentionItem]
    ):

        ATTENTION_PATH.write_text(

            json.dumps(
                [
                    item.model_dump()
                    for item in items
                ],
                ensure_ascii=False,
                indent=2
            ),

            encoding="utf-8"
        )


    # ==========================================
    # 加入Attention Queue
    # ==========================================

    def add(
        self,
        goal_id: str,
        kind: str,
        message: str,
        todo_id: str | None = None,
        details: dict | None = None
    ) -> AttentionItem:

        items = self._load()


        # ======================================
        # 相同问题已经OPEN
        # 不重复刷队列
        # ======================================

        for item in items:

            if (
                item.status
                ==
                "OPEN"
                and
                item.goal_id
                ==
                goal_id
                and
                item.todo_id
                ==
                todo_id
                and
                item.kind
                ==
                kind
            ):

                return item


        attention = AttentionItem(

            attention_id=(
                uuid4().hex[:10]
            ),

            goal_id=
                goal_id,

            todo_id=
                todo_id,

            kind=
                kind,

            message=
                message,

            details=
                details or {},

            status=
                "OPEN",

            created_at=
                self._now()
        )


        items.append(
            attention
        )


        self._save(
            items
        )


        return attention


    # ==========================================
    # 获取OPEN问题
    # ==========================================

    def get_open(
        self,
        goal_id: str | None = None
    ) -> list[AttentionItem]:

        items = self._load()


        return [

            item

            for item
            in items

            if (
                item.status
                ==
                "OPEN"
                and
                (
                    goal_id is None
                    or
                    item.goal_id
                    ==
                    goal_id
                )
            )
        ]


    # ==========================================
    # Resolve一个Attention
    # ==========================================

    def resolve(
        self,
        attention_id: str
    ) -> bool:

        items = self._load()

        found = False


        for item in items:

            if (
                item.attention_id
                ==
                attention_id
                and
                item.status
                ==
                "OPEN"
            ):

                item.status = (
                    "RESOLVED"
                )

                item.resolved_at = (
                    self._now()
                )

                found = True


        if found:

            self._save(
                items
            )


        return found


    # ==========================================
    # 自动解决某一类问题
    # ==========================================

    def resolve_matching(
        self,
        goal_id: str,
        kind: str,
        todo_id: str | None = None
    ):

        items = self._load()

        changed = False


        for item in items:

            if (
                item.status
                ==
                "OPEN"
                and
                item.goal_id
                ==
                goal_id
                and
                item.todo_id
                ==
                todo_id
                and
                item.kind
                ==
                kind
            ):

                item.status = (
                    "RESOLVED"
                )

                item.resolved_at = (
                    self._now()
                )

                changed = True


        if changed:

            self._save(
                items
            )


    def render_open(
        self,
        goal_id: str | None = None
    ) -> str:

        items = self.get_open(
            goal_id
        )


        if not items:

            return (
                "暂无需要人工关注的问题。"
            )


        lines = []


        for item in items:

            lines.append(
                (
                    f"[OPEN] "
                    f"{item.kind} | "
                    f"Todo={item.todo_id} | "
                    f"{item.message}"
                )
            )


        return "\n".join(
            lines
        )
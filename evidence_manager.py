import json

from datetime import datetime
from pathlib import Path
from uuid import uuid4

from pydantic import (
    BaseModel,
    Field
)


BASE_DIR = Path(
    __file__
).resolve().parent


EVIDENCE_DIR = (
    BASE_DIR
    / "evidence"
)


EVIDENCE_DIR.mkdir(
    exist_ok=True
)


class EvidenceRecord(
    BaseModel
):

    evidence_id: str

    goal_id: str

    todo_id: str

    kind: str

    passed: bool

    summary: str

    data: dict = Field(
        default_factory=dict
    )

    created_at: str


class EvidenceStore:

    # ==========================================
    # 当前时间
    # ==========================================

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
    # 每个Goal单独一个Evidence文件
    # ==========================================

    def _path(
        self,
        goal_id: str
    ) -> Path:

        return (
            EVIDENCE_DIR
            /
            f"{goal_id}.json"
        )


    # ==========================================
    # 读取Evidence
    # ==========================================

    def _load(
        self,
        goal_id: str
    ) -> list[EvidenceRecord]:

        path = (
            self._path(
                goal_id
            )
        )


        if not path.exists():

            return []


        try:

            data = json.loads(

                path.read_text(
                    encoding="utf-8"
                )
            )


            return [

                EvidenceRecord
                .model_validate(
                    item
                )

                for item
                in data
            ]


        except Exception:

            return []


    # ==========================================
    # 保存Evidence
    # ==========================================

    def _save(
        self,
        goal_id: str,
        records: list[EvidenceRecord]
    ):

        path = (
            self._path(
                goal_id
            )
        )


        path.write_text(

            json.dumps(

                [
                    item.model_dump()

                    for item
                    in records
                ],

                ensure_ascii=False,
                indent=2
            ),

            encoding="utf-8"
        )


    # ==========================================
    # 新增一条Evidence
    # ==========================================

    def add(
        self,
        goal_id: str,
        todo_id: str,
        kind: str,
        passed: bool,
        summary: str,
        data: dict | None = None
    ) -> EvidenceRecord:

        records = (
            self._load(
                goal_id
            )
        )


        record = EvidenceRecord(

            evidence_id=(
                uuid4()
                .hex[:10]
            ),

            goal_id=
                goal_id,

            todo_id=
                todo_id,

            kind=
                kind,

            passed=
                passed,

            summary=
                summary,

            data=
                data or {},

            created_at=
                self._now()
        )


        records.append(
            record
        )


        self._save(
            goal_id,
            records
        )


        return record


    # ==========================================
    # 获取全部Evidence
    # ==========================================

    def list(
        self,
        goal_id: str
    ) -> list[EvidenceRecord]:

        return (
            self._load(
                goal_id
            )
        )


    # ==========================================
    # 获取某种Evidence最新的一条
    # ==========================================

    def latest(
        self,
        goal_id: str,
        kind: str
    ) -> EvidenceRecord | None:

        records = (
            self._load(
                goal_id
            )
        )


        for record in reversed(
            records
        ):

            if (
                record.kind
                ==
                kind
            ):

                return record


        return None


    # ==========================================
    # 终端展示
    # ==========================================

    def render(
        self,
        goal_id: str
    ) -> str:

        records = (
            self._load(
                goal_id
            )
        )


        if not records:

            return (
                "暂无Evidence。"
            )


        lines = []


        for record in records:

            state = (
                "PASS"

                if record.passed

                else
                "FAIL"
            )


            lines.append(

                (
                    f"[{state}] "
                    f"{record.kind} | "
                    f"{record.summary}"
                )
            )


        return "\n".join(
            lines
        )
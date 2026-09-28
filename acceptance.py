import json

from datetime import datetime
from pathlib import Path

from evidence_manager import (
    EvidenceStore
)

from goal_state import (
    GoalManager
)

from attention_queue import (
    AttentionQueue
)

from protection import (
    check_protected_changes
)


BASE_DIR = Path(
    __file__
).resolve().parent


ACCEPTED_DIR = (
    BASE_DIR
    / "accepted"
)


ACCEPTED_DIR.mkdir(
    exist_ok=True
)


class AcceptanceGate:

    def __init__(
        self,
        evidence_store: EvidenceStore,
        attention_queue: AttentionQueue
    ):

        self.evidence_store = (
            evidence_store
        )

        self.attention_queue = (
            attention_queue
        )


    def evaluate(
        self,
        goal_manager: GoalManager
    ) -> dict:

        goal = (
            goal_manager.goal
        )


        if goal is None:

            return {

                "accepted":
                    False,

                "reason":
                    "no_goal"
            }


        # ======================================
        # 1. Todos必须全部DONE
        # ======================================

        if not (
            goal_manager
            .all_todos_done()
        ):

            return {

                "accepted":
                    False,

                "reason":
                    "todos_not_done"
            }


        # ======================================
        # 2. Day75：
        # Protected Paths检查
        # ======================================

        protection = (
            check_protected_changes()
        )


        self.evidence_store.add(

            goal_id=
                goal.goal_id,

            todo_id=
                "verify",

            kind=
                "PROTECTED_PATHS",

            passed=
                protection[
                    "passed"
                ],

            summary=(

                "Protected Paths未被修改"

                if protection[
                    "passed"
                ]

                else

                (
                    "检测到Protected Path被修改："
                    +
                    ", ".join(
                        protection[
                            "violations"
                        ]
                    )
                )
            ),

            data=
                protection
        )


        if not protection[
            "passed"
        ]:

            return {

                "accepted":
                    False,

                "reason":
                    "protected_path_modified",

                "violations":
                    protection[
                        "violations"
                    ]
            }


        # ======================================
        # 3. Git Diff Evidence
        # ======================================

        diff_evidence = (
            self.evidence_store
            .latest(
                goal.goal_id,
                "GIT_DIFF"
            )
        )


        if diff_evidence is None:

            return {

                "accepted":
                    False,

                "reason":
                    "missing_git_diff"
            }


        if not (
            diff_evidence.passed
        ):

            return {

                "accepted":
                    False,

                "reason":
                    "git_diff_not_accepted"
            }


        if not (
            diff_evidence.data.get(
                "has_changes",
                False
            )
        ):

            return {

                "accepted":
                    False,

                "reason":
                    "no_code_changes"
            }


        # ======================================
        # 4. Verification Evidence
        # ======================================

        verify_evidence = (
            self.evidence_store
            .latest(
                goal.goal_id,
                "VERIFICATION"
            )
        )


        if verify_evidence is None:

            return {

                "accepted":
                    False,

                "reason":
                    "missing_verification"
            }


        if not (
            verify_evidence.passed
        ):

            return {

                "accepted":
                    False,

                "reason":
                    "verification_failed"
            }


        if (
            verify_evidence.data.get(
                "status"
            )
            !=
            "PASS"
        ):

            return {

                "accepted":
                    False,

                "reason":
                    "verification_not_pass"
            }


        # ======================================
        # 5. Open Attention
        # ======================================

        open_attention = (
            self.attention_queue
            .get_open(
                goal.goal_id
            )
        )


        if open_attention:

            return {

                "accepted":
                    False,

                "reason":
                    "open_attention",

                "attention_count":
                    len(
                        open_attention
                    )
            }


        # ======================================
        # Accepted
        # ======================================

        return {

            "accepted":
                True,

            "reason":
                "evidence_accepted",

            "summary": {

                "git_diff_evidence_id":
                    diff_evidence
                    .evidence_id,

                "verification_evidence_id":
                    verify_evidence
                    .evidence_id,

                "verification_status":
                    verify_evidence
                    .data.get(
                        "status"
                    ),

                "changed_files":
                    protection[
                        "changed_files"
                    ],

                "protected_paths":
                    protection[
                        "protected_paths"
                    ]
            }
        }


    def writeback(
        self,
        goal_manager: GoalManager,
        gate_result: dict
    ) -> dict:

        if not (
            gate_result.get(
                "accepted",
                False
            )
        ):

            return {

                "written":
                    False,

                "reason":
                    "not_accepted"
            }


        goal = (
            goal_manager.goal
        )


        if goal is None:

            return {

                "written":
                    False,

                "reason":
                    "no_goal"
            }


        accepted_at = (

            datetime.now()
            .isoformat(
                timespec="seconds"
            )
        )


        record = {

            "goal_id":
                goal.goal_id,

            "objective":
                goal.objective,

            "accepted":
                True,

            "accepted_at":
                accepted_at,

            "acceptance":
                gate_result
        }


        path = (

            ACCEPTED_DIR

            /

            f"{goal.goal_id}.json"
        )


        path.write_text(

            json.dumps(

                record,

                ensure_ascii=False,

                indent=2
            ),

            encoding="utf-8"
        )


        goal_manager.mark_goal_accepted(
            gate_result
        )


        return {

            "written":
                True,

            "path":
                str(
                    path
                ),

            "accepted_at":
                accepted_at
        }
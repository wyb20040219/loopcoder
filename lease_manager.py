from datetime import (
    datetime,
    timedelta,
    timezone
)

from uuid import (
    uuid4
)

from goal_state import (
    GoalManager
)


class LeaseManager:

    def __init__(
        self,
        goal_manager: GoalManager,
        lease_seconds: int = 300
    ):

        self.goal_manager = (
            goal_manager
        )

        self.lease_seconds = (
            lease_seconds
        )


    def _now(
        self
    ) -> datetime:

        return datetime.now(
            timezone.utc
        )


    def _new_expiry(
        self
    ) -> str:

        expiry = (
            self._now()
            +
            timedelta(
                seconds=
                    self.lease_seconds
            )
        )

        return expiry.isoformat()


    def _is_expired(
        self,
        lease_expires_at: str | None
    ) -> bool:

        if not lease_expires_at:
            return True

        try:

            expiry = (
                datetime.fromisoformat(
                    lease_expires_at
                )
            )

            return (
                self._now()
                >=
                expiry
            )

        except Exception:

            return True


    # ==========================================
    # Claim Todo
    # ==========================================

    def claim(
        self,
        todo_id: str,
        worker_id: str
    ) -> dict:

        todo = (
            self.goal_manager
            .get_todo(
                todo_id
            )
        )

        if todo is None:

            return {
                "claimed": False,
                "reason": "todo_not_found"
            }


        if todo.status in {
            "DONE",
            "BLOCKED"
        }:

            return {
                "claimed": False,
                "reason":
                    f"todo_{todo.status.lower()}"
            }


        lease_expired = (
            self._is_expired(
                todo.lease_expires_at
            )
        )


        # ======================================
        # 其他Worker持有有效Lease
        # ======================================

        if (
            todo.claimed_by
            and
            todo.claimed_by
            !=
            worker_id
            and
            not lease_expired
        ):

            return {
                "claimed": False,

                "reason":
                    "lease_conflict",

                "owner":
                    todo.claimed_by,

                "lease_expires_at":
                    todo.lease_expires_at
            }


        # ======================================
        # 同一个Worker继续持有有效Lease
        # ======================================

        if (
            todo.claimed_by
            ==
            worker_id
            and
            todo.lease_id
            and
            not lease_expired
        ):

            todo.lease_expires_at = (
                self._new_expiry()
            )

            self.goal_manager.save()

            return {
                "claimed": True,

                "reason":
                    "lease_renewed",

                "lease_id":
                    todo.lease_id,

                "lease_expires_at":
                    todo.lease_expires_at
            }


        # ======================================
        # 无Owner / Lease已过期
        #
        # 创建新的Claim
        # ======================================

        todo.claimed_by = (
            worker_id
        )

        todo.lease_id = (
            uuid4().hex
        )

        todo.lease_expires_at = (
            self._new_expiry()
        )

        todo.status = (
            "RUNNING"
        )


        if self.goal_manager.goal:

            self.goal_manager.goal.current_todo_id = (
                todo_id
            )


        self.goal_manager.save()


        return {
            "claimed": True,

            "reason":
                (
                    "lease_taken_over"
                    if lease_expired
                    else
                    "lease_created"
                ),

            "lease_id":
                todo.lease_id,

            "lease_expires_at":
                todo.lease_expires_at
        }


    # ==========================================
    # 验证当前Worker是否仍然拥有执行权
    # ==========================================

    def validate(
        self,
        todo_id: str,
        worker_id: str,
        lease_id: str
    ) -> bool:

        todo = (
            self.goal_manager
            .get_todo(
                todo_id
            )
        )

        if todo is None:
            return False


        if (
            todo.claimed_by
            !=
            worker_id
        ):

            return False


        if (
            todo.lease_id
            !=
            lease_id
        ):

            return False


        if self._is_expired(
            todo.lease_expires_at
        ):

            return False


        return True


    # ==========================================
    # 续租
    # ==========================================

    def renew(
        self,
        todo_id: str,
        worker_id: str,
        lease_id: str
    ) -> dict:

        if not self.validate(
            todo_id=
                todo_id,

            worker_id=
                worker_id,

            lease_id=
                lease_id
        ):

            return {
                "renewed": False,
                "reason":
                    "invalid_or_expired_lease"
            }


        todo = (
            self.goal_manager
            .get_todo(
                todo_id
            )
        )


        todo.lease_expires_at = (
            self._new_expiry()
        )


        self.goal_manager.save()


        return {
            "renewed": True,
            "lease_expires_at":
                todo.lease_expires_at
        }


    # ==========================================
    # 主动释放
    # ==========================================

    def release(
        self,
        todo_id: str,
        worker_id: str,
        lease_id: str
    ) -> bool:

        if not self.validate(
            todo_id,
            worker_id,
            lease_id
        ):

            return False


        todo = (
            self.goal_manager
            .get_todo(
                todo_id
            )
        )


        todo.claimed_by = None
        todo.lease_id = None
        todo.lease_expires_at = None


        self.goal_manager.save()


        return True
import time


class QuotaManager:

    def __init__(
        self,
        max_ticks: int = 12,
        max_llm_calls: int = 8,
        max_tool_calls: int = 20,
        max_verify_calls: int = 4,
        max_runtime_seconds: float = 300
    ):

        # ======================================
        # Quota Limits
        # ======================================

        self.limits = {

            "ticks":
                max_ticks,

            "llm_calls":
                max_llm_calls,

            "tool_calls":
                max_tool_calls,

            "verify_calls":
                max_verify_calls,

            "runtime_seconds":
                float(
                    max_runtime_seconds
                )
        }


        # ======================================
        # 当前已经用了多少
        # ======================================

        self.usage = {

            "ticks": 0,

            "llm_calls": 0,

            "tool_calls": 0,

            "verify_calls": 0,

            "runtime_seconds": 0.0
        }


        # perf_counter只用于计算
        # 当前Python进程实际运行时间
        self._last_runtime_mark = (
            time.perf_counter()
        )


    # ==========================================
    # 同步Runtime时间
    # ==========================================

    def _sync_runtime(
        self
    ):

        now = (
            time.perf_counter()
        )


        delta = (
            now
            -
            self._last_runtime_mark
        )


        if delta > 0:

            self.usage[
                "runtime_seconds"
            ] += delta


        self._last_runtime_mark = (
            now
        )


    # ==========================================
    # 当前状态快照
    # ==========================================

    def snapshot(
        self
    ) -> dict:

        self._sync_runtime()


        remaining = {}


        for key in (
            "ticks",
            "llm_calls",
            "tool_calls",
            "verify_calls"
        ):

            remaining[key] = max(

                0,

                self.limits[key]
                -
                self.usage[key]
            )


        remaining[
            "runtime_seconds"
        ] = max(

            0.0,

            self.limits[
                "runtime_seconds"
            ]
            -
            self.usage[
                "runtime_seconds"
            ]
        )


        return {

            "limits":
                dict(
                    self.limits
                ),

            "usage":
                dict(
                    self.usage
                ),

            "remaining":
                remaining
        }


    # ==========================================
    # 尝试消费Quota
    #
    # resources可以同时传多个：
    #
    # ["tool_calls", "verify_calls"]
    #
    # 要么全部成功，
    # 要么全部不扣
    # ==========================================

    def try_consume(
        self,
        resources: list[str]
    ) -> dict:

        self._sync_runtime()


        # ======================================
        # 第一层：
        # 总运行时间是否已经超预算
        # ======================================

        if (
            self.usage[
                "runtime_seconds"
            ]
            >=
            self.limits[
                "runtime_seconds"
            ]
        ):

            return {

                "allowed": False,

                "reason":
                    "quota_exhausted",

                "resource":
                    "runtime_seconds",

                "status":
                    self.snapshot()
            }


        # ======================================
        # 先全部检查
        #
        # 此时还不扣Quota
        # ======================================

        for resource in resources:

            if resource not in (
                "ticks",
                "llm_calls",
                "tool_calls",
                "verify_calls"
            ):

                return {

                    "allowed": False,

                    "reason":
                        "unknown_quota_resource",

                    "resource":
                        resource,

                    "status":
                        self.snapshot()
                }


            if (
                self.usage[
                    resource
                ]
                >=
                self.limits[
                    resource
                ]
            ):

                return {

                    "allowed": False,

                    "reason":
                        "quota_exhausted",

                    "resource":
                        resource,

                    "status":
                        self.snapshot()
                }


        # ======================================
        # 所有资源都还有预算
        #
        # 才一起扣
        # ======================================

        for resource in resources:

            self.usage[
                resource
            ] += 1


        return {

            "allowed": True,

            "reason":
                "quota_consumed",

            "consumed":
                resources,

            "status":
                self.snapshot()
        }


    # ==========================================
    # 只检查Runtime时间
    # 不消费计数Quota
    # ==========================================

    def check_runtime(
        self
    ) -> dict:

        self._sync_runtime()


        if (
            self.usage[
                "runtime_seconds"
            ]
            >=
            self.limits[
                "runtime_seconds"
            ]
        ):

            return {

                "allowed": False,

                "reason":
                    "quota_exhausted",

                "resource":
                    "runtime_seconds",

                "status":
                    self.snapshot()
            }


        return {

            "allowed": True,

            "reason":
                "runtime_available",

            "status":
                self.snapshot()
        }


    # ==========================================
    # 给Checkpoint保存
    # ==========================================

    def export_state(
        self
    ) -> dict:

        self._sync_runtime()


        return {

            "limits":
                dict(
                    self.limits
                ),

            "usage":
                dict(
                    self.usage
                )
        }


    # ==========================================
    # 从Checkpoint恢复
    # ==========================================

    def import_state(
        self,
        state: dict
    ):

        saved_limits = (
            state.get(
                "limits"
            )
        )


        saved_usage = (
            state.get(
                "usage"
            )
        )


        if isinstance(
            saved_limits,
            dict
        ):

            for key in self.limits:

                if key in saved_limits:

                    self.limits[key] = (
                        saved_limits[key]
                    )


        if isinstance(
            saved_usage,
            dict
        ):

            for key in self.usage:

                if key in saved_usage:

                    self.usage[key] = (
                        saved_usage[key]
                    )


        # 恢复以后重新从当前时间开始
        # 计算本次进程运行时长
        self._last_runtime_mark = (
            time.perf_counter()
        )


    # ==========================================
    # 终端展示
    # ==========================================

    def render(
        self
    ) -> str:

        status = (
            self.snapshot()
        )


        lines = [
            "Quota:"
        ]


        for key in (
            "ticks",
            "llm_calls",
            "tool_calls",
            "verify_calls"
        ):

            lines.append(

                f"- {key}: "
                f"{status['usage'][key]}"
                f"/"
                f"{status['limits'][key]}"
            )


        lines.append(

            "- runtime_seconds: "
            f"{status['usage']['runtime_seconds']:.1f}"
            "/"
            f"{status['limits']['runtime_seconds']:.1f}"
        )


        return "\n".join(
            lines
        )
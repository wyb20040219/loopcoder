from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    messages_to_dict,
    messages_from_dict
)


class ContextManager:

    def __init__(
        self,
        system_prompt: str,
        user_goal: str,
        max_recent_steps: int = 4,
        max_history_items: int = 20,
        max_result_chars: int = 800
    ):

        self.system_prompt = (
            system_prompt
        )

        self.user_goal = (
            user_goal
        )

        # 最近保留几个完整Agent Step
        self.max_recent_steps = (
            max_recent_steps
        )

        # 最多保留多少条旧历史摘要
        self.max_history_items = (
            max_history_items
        )

        # 每条旧Tool结果摘要最多多少字符
        self.max_result_chars = (
            max_result_chars
        )

        # 已被压缩的旧历史
        self.history_summary = []

        # 最近完整Agent Step
        self.recent_steps = []


    # ==========================================
    # 添加一个完整Agent Step
    # ==========================================

    def add_step(
        self,
        ai_message,
        tool_records: list
    ):

        summaries = (
            self._build_summaries(
                tool_records
            )
        )


        self.recent_steps.append(
            {
                "ai_message":
                    ai_message,

                "tool_records":
                    tool_records,

                "summaries":
                    summaries
            }
        )


        self._trim_steps()


    # ==========================================
    # 把本轮Tool结果转成简短摘要
    # ==========================================

    def _build_summaries(
        self,
        tool_records: list
    ) -> list:

        summaries = []


        for record in tool_records:

            result_text = str(
                record[
                    "result"
                ]
            )


            if (
                len(result_text)
                >
                self.max_result_chars
            ):

                result_text = (
                    result_text[
                        :self.max_result_chars
                    ]
                    +
                    "...[truncated]"
                )


            summaries.append(
                {
                    "tool_name":
                        record[
                            "tool_name"
                        ],

                    "tool_args":
                        record[
                            "tool_args"
                        ],

                    "result":
                        result_text
                }
            )


        return summaries


    # ==========================================
    # recent_steps太多时
    # 把最老的完整Step移到摘要区
    # ==========================================

    def _trim_steps(
        self
    ):

        while (
            len(
                self.recent_steps
            )
            >
            self.max_recent_steps
        ):

            old_step = (
                self.recent_steps.pop(
                    0
                )
            )


            self.history_summary.extend(
                old_step[
                    "summaries"
                ]
            )


        self._trim_history()


    # ==========================================
    # 防止history_summary也无限增长
    # ==========================================

    def _trim_history(
        self
    ):

        if (
            len(
                self.history_summary
            )
            >
            self.max_history_items
        ):

            self.history_summary = (
                self.history_summary[
                    -self.max_history_items:
                ]
            )


    # ==========================================
    # 构造真正发送给LLM的messages
    # ==========================================

    def build_messages(
        self
    ) -> list:

        messages = [
            SystemMessage(
                content=
                    self.system_prompt
            ),

            HumanMessage(
                content=(
                    "当前任务：\n"
                    f"{self.user_goal}"
                )
            )
        ]


        # ======================================
        # 较早历史：
        # 只发送压缩摘要
        # ======================================

        if self.history_summary:

            summary_text = (
                "以下是较早的Agent执行摘要。"
                "这些步骤已经执行过，"
                "不要无意义重复：\n"
            )


            for index, item in enumerate(
                self.history_summary,
                start=1
            ):

                summary_text += (
                    f"\n[{index}] "
                    f"Tool: "
                    f"{item['tool_name']}"
                    f"\nArgs: "
                    f"{item['tool_args']}"
                    f"\nResult: "
                    f"{item['result']}"
                    f"\n"
                )


            messages.append(
                HumanMessage(
                    content=
                        summary_text
                )
            )


        # ======================================
        # 最近历史：
        # 保留完整协议结构
        # ======================================

        for step in (
            self.recent_steps
        ):

            messages.append(
                step[
                    "ai_message"
                ]
            )


            for record in (
                step[
                    "tool_records"
                ]
            ):

                messages.append(
                    record[
                        "tool_message"
                    ]
                )


        return messages


    # ==========================================
    # 导出Context
    # 给Checkpoint保存
    # ==========================================

    def export_state(
        self
    ) -> dict:

        saved_steps = []


        for step in (
            self.recent_steps
        ):

            messages = [
                step[
                    "ai_message"
                ]
            ]


            for record in (
                step[
                    "tool_records"
                ]
            ):

                messages.append(
                    record[
                        "tool_message"
                    ]
                )


            tool_metadata = []


            for record in (
                step[
                    "tool_records"
                ]
            ):

                tool_metadata.append(
                    {
                        "tool_name":
                            record[
                                "tool_name"
                            ],

                        "tool_args":
                            record[
                                "tool_args"
                            ],

                        "result":
                            str(
                                record[
                                    "result"
                                ]
                            )
                    }
                )


            saved_steps.append(
                {
                    "messages":
                        messages_to_dict(
                            messages
                        ),

                    "tool_metadata":
                        tool_metadata,

                    "summaries":
                        step.get(
                            "summaries",
                            []
                        )
                }
            )


        return {
            "history_summary":
                self.history_summary,

            "recent_steps":
                saved_steps
        }


    # ==========================================
    # 从Checkpoint恢复Context
    # ==========================================

    def import_state(
        self,
        state: dict
    ):

        self.history_summary = (
            state.get(
                "history_summary",
                []
            )
        )


        self.recent_steps = []


        saved_steps = (
            state.get(
                "recent_steps",
                []
            )
        )


        for saved_step in (
            saved_steps
        ):

            messages = (
                messages_from_dict(
                    saved_step[
                        "messages"
                    ]
                )
            )


            ai_message = (
                messages[
                    0
                ]
            )


            tool_messages = (
                messages[
                    1:
                ]
            )


            tool_metadata = (
                saved_step.get(
                    "tool_metadata",
                    []
                )
            )


            tool_records = []


            for index, tool_message in enumerate(
                tool_messages
            ):

                if (
                    index
                    <
                    len(
                        tool_metadata
                    )
                ):

                    metadata = (
                        tool_metadata[
                            index
                        ]
                    )


                else:

                    metadata = {
                        "tool_name": "",
                        "tool_args": {},
                        "result":
                            tool_message.content
                    }


                tool_records.append(
                    {
                        "tool_name":
                            metadata.get(
                                "tool_name",
                                ""
                            ),

                        "tool_args":
                            metadata.get(
                                "tool_args",
                                {}
                            ),

                        "result":
                            metadata.get(
                                "result",
                                tool_message.content
                            ),

                        "tool_message":
                            tool_message
                    }
                )


            self.recent_steps.append(
                {
                    "ai_message":
                        ai_message,

                    "tool_records":
                        tool_records,

                    "summaries":
                        saved_step.get(
                            "summaries",
                            []
                        )
                }
            )


        # 恢复后也重新执行一次限制
        self._trim_steps()


    # ==========================================
    # 调试信息
    # ==========================================

    def get_debug_info(
        self
    ) -> dict:

        return {
            "history_summary_count":
                len(
                    self.history_summary
                ),

            "recent_steps_count":
                len(
                    self.recent_steps
                ),

            "max_recent_steps":
                self.max_recent_steps,

            "max_history_items":
                self.max_history_items
        }
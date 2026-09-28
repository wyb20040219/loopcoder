import json

from datetime import datetime
from pathlib import Path
from uuid import uuid4


BASE_DIR = Path(
    __file__
).resolve().parent


TRACE_DIR = (
    BASE_DIR
    / "traces"
)


TRACE_DIR.mkdir(
    exist_ok=True
)


class TraceRecorder:

    def __init__(
        self,
        task_name: str
    ):

        # ======================================
        # Day76：
        # 微秒 + UUID
        #
        # 防止Benchmark连续Run时文件名碰撞
        # ======================================

        timestamp = (
            datetime.now()
            .strftime(
                "%Y%m%d_%H%M%S_%f"
            )
        )


        suffix = (
            uuid4()
            .hex[:6]
        )


        self.trace_path = (

            TRACE_DIR

            /

            (
                f"{timestamp}_"
                f"{suffix}_"
                f"{task_name}.jsonl"
            )
        )


    def record(
        self,
        event_type: str,
        data: dict
    ):

        event = {

            "time":
                datetime.now()
                .isoformat(),

            "event_type":
                event_type,

            "data":
                data
        }


        with self.trace_path.open(
            "a",
            encoding="utf-8"
        ) as f:

            f.write(

                json.dumps(
                    event,
                    ensure_ascii=False
                )

                +

                "\n"
            )
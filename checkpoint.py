import json

from pathlib import Path


BASE_DIR = Path(
    __file__
).resolve().parent


CHECKPOINT_DIR = (
    BASE_DIR
    / "checkpoints"
)


CHECKPOINT_DIR.mkdir(
    exist_ok=True
)


CHECKPOINT_PATH = (
    CHECKPOINT_DIR
    / "agent_checkpoint.json"
)


def save_checkpoint(
    data: dict
) -> dict:

    try:

        CHECKPOINT_PATH.write_text(
            json.dumps(
                data,
                ensure_ascii=False,
                indent=2
            ),
            encoding="utf-8"
        )


        return {
            "success": True,
            "path": str(
                CHECKPOINT_PATH
            )
        }


    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }


def load_checkpoint() -> dict | None:

    if not CHECKPOINT_PATH.exists():

        return None


    try:

        content = (
            CHECKPOINT_PATH.read_text(
                encoding="utf-8"
            )
        )


        return json.loads(
            content
        )


    except Exception as e:

        print(
            "读取Checkpoint失败：",
            e
        )

        return None


def clear_checkpoint():

    if CHECKPOINT_PATH.exists():

        CHECKPOINT_PATH.unlink()
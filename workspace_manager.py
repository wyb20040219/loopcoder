import shutil
import subprocess

from datetime import datetime
from pathlib import Path
from uuid import uuid4


BASE_DIR = Path(
    __file__
).resolve().parent


RUNS_DIR = (
    BASE_DIR
    / "runs"
)


RUNS_DIR.mkdir(
    exist_ok=True
)


def run_git(
    workspace: Path,
    args: list[str]
) -> dict:

    try:

        result = (
            subprocess.run(

                [
                    "git",
                    *args
                ],

                cwd=str(
                    workspace
                ),

                capture_output=True,

                text=True,

                timeout=15
            )
        )


        return {

            "success":
                result.returncode
                ==
                0,

            "returncode":
                result.returncode,

            "stdout":
                result.stdout,

            "stderr":
                result.stderr
        }


    except Exception as e:

        return {

            "success":
                False,

            "returncode":
                None,

            "stdout":
                "",

            "stderr":
                str(e)
        }


def prepare_run(
    source_repo: str | Path
) -> dict:

    source_repo = Path(
        source_repo
    ).resolve()


    if not source_repo.exists():

        raise FileNotFoundError(
            f"Source Repo不存在：{source_repo}"
        )


    if not source_repo.is_dir():

        raise ValueError(
            "Source Repo必须是目录"
        )


    timestamp = (
        datetime.now()
        .strftime(
            "%Y%m%d_%H%M%S"
        )
    )


    run_id = (

        "run_"
        +
        timestamp
        +
        "_"
        +
        uuid4().hex[:6]
    )


    run_dir = (
        RUNS_DIR
        /
        run_id
    )


    workspace = (
        run_dir
        /
        "workspace"
    )


    shutil.copytree(

        source_repo,

        workspace,

        ignore=shutil.ignore_patterns(

            ".git",

            ".venv",

            "__pycache__",

            ".pytest_cache",

            ".mypy_cache",

            ".ruff_cache"
        )
    )


    # ======================================
    # 为这次Run创建独立Git Baseline
    # ======================================

    result = (
        run_git(
            workspace,
            [
                "init"
            ]
        )
    )


    if not result[
        "success"
    ]:

        raise RuntimeError(
            "Git init失败："
            +
            result[
                "stderr"
            ]
        )


    run_git(
        workspace,
        [
            "config",
            "user.email",
            "loopcoder@example.com"
        ]
    )


    run_git(
        workspace,
        [
            "config",
            "user.name",
            "LoopCoder Runtime"
        ]
    )


    run_git(
        workspace,
        [
            "add",
            "."
        ]
    )


    commit_result = (
        run_git(
            workspace,
            [
                "commit",
                "-m",
                "run baseline"
            ]
        )
    )


    if not commit_result[
        "success"
    ]:

        raise RuntimeError(
            "创建Run Git Baseline失败："
            +
            commit_result[
                "stderr"
            ]
        )


    return {

        "run_id":
            run_id,

        "source_repo":
            str(
                source_repo
            ),

        "run_dir":
            str(
                run_dir
            ),

        "workspace":
            str(
                workspace
            )
    }
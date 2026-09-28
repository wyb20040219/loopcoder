import os

from pathlib import Path


BASE_DIR = Path(
    __file__
).resolve().parent


DEFAULT_WORKSPACE = (
    BASE_DIR
    / "workspace"
).resolve()


def get_workspace() -> Path:

    """
    返回当前 Agent Run 应该使用的 Workspace。

    优先读取环境变量：

        AGENT_WORKSPACE

    如果没有设置，
    继续兼容以前的：

        day63/workspace
    """

    configured = (
        os.getenv(
            "AGENT_WORKSPACE",
            ""
        )
        .strip()
    )


    if configured:

        workspace = Path(
            configured
        ).resolve()


    else:

        workspace = (
            DEFAULT_WORKSPACE
        )


    workspace.mkdir(
        parents=True,
        exist_ok=True
    )


    return workspace
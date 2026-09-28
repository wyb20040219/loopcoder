from langchain_core.tools import tool

from filesystem_tools import (
    list_files as _list_files,
    read_file as _read_file,
    write_file as _write_file,
    replace_text as _replace_text
)

from verification import (
    verify_command
)

from git_tools import (
    git_diff as _git_diff
)

@tool
def git_diff() -> dict:
    """
    查看当前工作区相对于 Git 基线的代码修改。

    在修改代码后，可以使用此工具审查实际变更。
    """

    return _git_diff()

@tool
def list_files() -> dict:
    """
    列出当前代码工作区中的所有文件。
    """

    return _list_files()


@tool
def read_file(
    file_path: str
) -> dict:
    """
    读取工作区中的文本文件。

    Args:
        file_path:
            相对于 Workspace 的文件路径。
    """

    return _read_file(
        file_path
    )


@tool
def write_file(
    file_path: str,
    content: str
) -> dict:
    """
    创建新文件或完整覆盖一个文件。

    只有在创建新文件，
    或确实需要完整重写文件时使用。

    Args:
        file_path:
            相对于 Workspace 的文件路径。

        content:
            要写入的完整内容。
    """

    return _write_file(
        file_path,
        content
    )


@tool
def replace_text(
    file_path: str,
    old_text: str,
    new_text: str
) -> dict:
    """
    精确替换文件中的一段代码。

    修改已有代码时优先使用此工具，
    不要无必要地完整重写整个文件。

    Args:
        file_path:
            相对于 Workspace 的文件路径。

        old_text:
            原文件中精确存在的文本。

        new_text:
            用于替换的新文本。
    """

    return _replace_text(
        file_path=file_path,
        old_text=old_text,
        new_text=new_text
    )


@tool
def verify_project(
    command: list[str]
) -> dict:
    """
    在 Docker Sandbox 中正式验证项目。

    当准备判断任务是否完成时，
    必须调用此工具。

    Args:
        command:
            验证命令。

            Python项目通常使用：
            ["python", "-m", "pytest", "-q"]
    """

    return verify_command(
        command
    )


TOOLS = [
    list_files,
    read_file,
    write_file,
    replace_text,
    git_diff,
    verify_project
]


TOOL_MAP = {
    tool.name: tool
    for tool in TOOLS
}
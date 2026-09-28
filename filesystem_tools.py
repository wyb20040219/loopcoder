from pathlib import Path

from runtime_paths import (
    get_workspace
)

from protection import (
    is_protected_path
)


IGNORED_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache"
}


def safe_path(
    relative_path: str
) -> Path:

    workspace = (
        get_workspace()
    )


    target = (
        workspace
        / relative_path
    ).resolve()


    if (
        target != workspace
        and
        workspace not in target.parents
    ):

        raise ValueError(
            "禁止访问 Workspace 之外的路径"
        )


    return target


def should_ignore(
    path: Path,
    workspace: Path
) -> bool:

    try:

        relative = (
            path.relative_to(
                workspace
            )
        )


    except ValueError:

        return True


    return any(

        part in IGNORED_DIRS

        for part
        in relative.parts
    )


def list_files() -> dict:

    try:

        workspace = (
            get_workspace()
        )


        files = []


        for path in (
            workspace.rglob("*")
        ):

            if should_ignore(
                path,
                workspace
            ):

                continue


            if path.is_file():

                files.append(

                    str(
                        path.relative_to(
                            workspace
                        )
                    )
                )


        files.sort()


        return {

            "success":
                True,

            "files":
                files,

            "error":
                ""
        }


    except Exception as e:

        return {

            "success":
                False,

            "files":
                [],

            "error":
                str(e)
        }


def read_file(
    file_path: str
) -> dict:

    try:

        path = (
            safe_path(
                file_path
            )
        )


        if not path.exists():

            return {

                "success":
                    False,

                "content":
                    "",

                "error":
                    "文件不存在"
            }


        if not path.is_file():

            return {

                "success":
                    False,

                "content":
                    "",

                "error":
                    "目标不是文件"
            }


        content = (
            path.read_text(
                encoding="utf-8"
            )
        )


        return {

            "success":
                True,

            "content":
                content,

            "error":
                ""
        }


    except Exception as e:

        return {

            "success":
                False,

            "content":
                "",

            "error":
                str(e)
        }


def write_file(
    file_path: str,
    content: str
) -> dict:

    # ======================================
    # Day75：
    # Protected Path硬拦截
    # ======================================

    if is_protected_path(
        file_path
    ):

        return {

            "success":
                False,

            "changed":
                False,

            "file_path":
                file_path,

            "error":
                (
                    "Protected Path："
                    "Runtime禁止修改该文件。"
                )
        }


    try:

        path = (
            safe_path(
                file_path
            )
        )


        path.parent.mkdir(
            parents=True,
            exist_ok=True
        )


        old_content = None


        if path.exists():

            old_content = (
                path.read_text(
                    encoding="utf-8"
                )
            )


        path.write_text(
            content,
            encoding="utf-8"
        )


        changed = (
            old_content
            !=
            content
        )


        return {

            "success":
                True,

            "changed":
                changed,

            "file_path":
                file_path,

            "error":
                ""
        }


    except Exception as e:

        return {

            "success":
                False,

            "changed":
                False,

            "file_path":
                file_path,

            "error":
                str(e)
        }


def replace_text(
    file_path: str,
    old_text: str,
    new_text: str
) -> dict:

    # ======================================
    # Day75：
    # Protected Path硬拦截
    # ======================================

    if is_protected_path(
        file_path
    ):

        return {

            "success":
                False,

            "changed":
                False,

            "file_path":
                file_path,

            "error":
                (
                    "Protected Path："
                    "Runtime禁止修改该文件。"
                )
        }


    try:

        path = (
            safe_path(
                file_path
            )
        )


        if not path.exists():

            return {

                "success":
                    False,

                "changed":
                    False,

                "error":
                    "文件不存在"
            }


        content = (
            path.read_text(
                encoding="utf-8"
            )
        )


        count = (
            content.count(
                old_text
            )
        )


        if count == 0:

            return {

                "success":
                    False,

                "changed":
                    False,

                "error":
                    "没有找到要替换的内容"
            }


        if count > 1:

            return {

                "success":
                    False,

                "changed":
                    False,

                "error":
                    (
                        f"待替换内容出现了 {count} 次，"
                        "拒绝进行不明确的修改"
                    )
            }


        if (
            old_text
            ==
            new_text
        ):

            return {

                "success":
                    True,

                "changed":
                    False,

                "file_path":
                    file_path,

                "replacements":
                    0,

                "error":
                    ""
            }


        new_content = (
            content.replace(
                old_text,
                new_text,
                1
            )
        )


        path.write_text(
            new_content,
            encoding="utf-8"
        )


        return {

            "success":
                True,

            "changed":
                True,

            "file_path":
                file_path,

            "replacements":
                1,

            "error":
                ""
        }


    except Exception as e:

        return {

            "success":
                False,

            "changed":
                False,

            "error":
                str(e)
        }
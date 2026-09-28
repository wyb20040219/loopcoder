import json
import os

from pathlib import Path

from git_tools import (
    git_status
)


# ==========================================
# 读取Protected Paths
# ==========================================

def get_protected_paths() -> list[str]:

    raw = (
        os.getenv(
            "AGENT_PROTECTED_PATHS",
            ""
        )
        .strip()
    )


    if not raw:

        return []


    # ======================================
    # 推荐格式：
    #
    # ["tests", ".github"]
    # ======================================

    try:

        data = json.loads(
            raw
        )


        if isinstance(
            data,
            list
        ):

            return [

                str(item)
                .replace("\\", "/")
                .strip("/")

                for item
                in data

                if str(item).strip()
            ]


    except json.JSONDecodeError:

        pass


    # ======================================
    # 兼容：
    #
    # tests,.github
    # ======================================

    return [

        item
        .strip()
        .replace("\\", "/")
        .strip("/")

        for item
        in raw.split(",")

        if item.strip()
    ]


# ==========================================
# 统一Path格式
# ==========================================

def normalize_repo_path(
    path: str
) -> str:

    return (
        path
        .replace("\\", "/")
        .strip("/")
    )


# ==========================================
# 判断路径是否Protected
# ==========================================

def is_protected_path(
    path: str
) -> bool:

    target = (
        normalize_repo_path(
            path
        )
    )


    protected_paths = (
        get_protected_paths()
    )


    for protected in (
        protected_paths
    ):

        protected = (
            normalize_repo_path(
                protected
            )
        )


        # ==================================
        # 精确文件
        #
        # tests/test_x.py
        # ==================================

        if (
            target
            ==
            protected
        ):

            return True


        # ==================================
        # 目录
        #
        # protected = tests
        #
        # target =
        # tests/test_user.py
        # ==================================

        if target.startswith(
            protected + "/"
        ):

            return True


    return False


# ==========================================
# 获取Git当前所有变化文件
# ==========================================

def get_changed_files() -> dict:

    result = (
        git_status()
    )


    if not result.get(
        "success",
        False
    ):

        return {

            "success":
                False,

            "files":
                [],

            "error":
                result.get(
                    "stderr",
                    ""
                )
        }


    changed_files = []


    stdout = (
        result.get(
            "stdout",
            ""
        )
    )


    for line in (
        stdout.splitlines()
    ):

        if not line.strip():

            continue


        # git status --short
        #
        # M  file.py
        # ?? new_file.py
        #
        # 前两个字符是状态
        path = (
            line[3:]
            .strip()
        )


        # ==================================
        # rename：
        #
        # old.py -> new.py
        # ==================================

        if " -> " in path:

            path = (
                path
                .split(
                    " -> ",
                    1
                )[1]
            )


        path = (
            normalize_repo_path(
                path
            )
        )


        if path:

            changed_files.append(
                path
            )


    return {

        "success":
            True,

        "files":
            sorted(
                set(
                    changed_files
                )
            ),

        "error":
            ""
    }


# ==========================================
# 检查Protected Paths有没有被改
# ==========================================

def check_protected_changes() -> dict:

    changed_result = (
        get_changed_files()
    )


    if not changed_result[
        "success"
    ]:

        return {

            "passed":
                False,

            "changed_files":
                [],

            "violations":
                [],

            "error":
                changed_result[
                    "error"
                ]
        }


    changed_files = (
        changed_result[
            "files"
        ]
    )


    violations = [

        path

        for path
        in changed_files

        if is_protected_path(
            path
        )
    ]


    return {

        "passed":
            len(
                violations
            )
            ==
            0,

        "changed_files":
            changed_files,

        "violations":
            violations,

        "protected_paths":
            get_protected_paths(),

        "error":
            ""
    }
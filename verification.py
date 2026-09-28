from sandbox import (
    run_in_sandbox
)


# ==========================================
# Verifier Argument Policy
# ==========================================

def is_safe_verification_command(
    command: list[str]
) -> bool:

    if not command:

        return False


    # ======================================
    # 禁止：
    #
    # python -c "..."
    #
    # 防止模型借Verifier偷偷修改代码
    # ======================================

    if "-c" in command:

        return False


    # ======================================
    # python -m pytest ...
    # ======================================

    if (

        len(command)
        >=
        3

        and

        command[0]
        in {
            "python",
            "python3"
        }

        and

        command[1]
        ==
        "-m"

        and

        command[2]
        ==
        "pytest"
    ):

        return True


    # ======================================
    # pytest ...
    # ======================================

    if (
        command[0]
        ==
        "pytest"
    ):

        return True


    return False


# ==========================================
# 判断是否是Docker/基础设施错误
# ==========================================

def looks_like_infra_error(
    returncode,
    stderr: str
) -> bool:

    if returncode is None:

        return True


    text = (
        stderr
        or
        ""
    ).lower()


    infra_keywords = [

        "cannot connect to the docker daemon",

        "error during connect",

        "docker daemon",

        "docker desktop",

        "dockerdesktoplinuxengine",

        "the system cannot find the file specified",

        "docker不可用"
    ]


    for keyword in (
        infra_keywords
    ):

        if keyword in text:

            return True


    # Docker CLI常见基础设施启动错误
    if returncode == 125:

        return True


    return False


# ==========================================
# Verification
# ==========================================

def verify_command(
    command: list[str],
    timeout: int = 30
) -> dict:

    # ======================================
    # 1. Argument Policy
    # ======================================

    if not (
        is_safe_verification_command(
            command
        )
    ):

        return {

            "passed":
                False,

            "status":
                "POLICY_DENIED",

            "command":
                command,

            "returncode":
                None,

            "stdout":
                "",

            "stderr":
                (
                    "Verification命令被安全策略拒绝。"
                    "只允许pytest验证命令。"
                )
        }


    # ======================================
    # 2. Docker Sandbox
    # ======================================

    result = (
        run_in_sandbox(

            command=
                command,

            timeout=
                timeout,

            read_only=
                True
        )
    )


    # ======================================
    # 3. Infrastructure Error
    # ======================================

    if (
        looks_like_infra_error(

            returncode=
                result[
                    "returncode"
                ],

            stderr=
                result[
                    "stderr"
                ]
        )
    ):

        return {

            "passed":
                False,

            "status":
                "INFRA_ERROR",

            "command":
                command,

            "returncode":
                result[
                    "returncode"
                ],

            "stdout":
                result[
                    "stdout"
                ],

            "stderr":
                result[
                    "stderr"
                ]
        }


    # ======================================
    # 4. Verification PASS
    # ======================================

    if (
        result[
            "returncode"
        ]
        ==
        0
    ):

        return {

            "passed":
                True,

            "status":
                "PASS",

            "command":
                command,

            "returncode":
                result[
                    "returncode"
                ],

            "stdout":
                result[
                    "stdout"
                ],

            "stderr":
                result[
                    "stderr"
                ]
        }


    # ======================================
    # 5. 测试真正失败
    # ======================================

    return {

        "passed":
            False,

        "status":
            "TEST_FAILED",

        "command":
            command,

        "returncode":
            result[
                "returncode"
            ],

        "stdout":
            result[
                "stdout"
            ],

        "stderr":
            result[
                "stderr"
            ]
    }
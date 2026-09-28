import subprocess

from runtime_paths import (
    get_workspace
)


SANDBOX_IMAGE = (
    "coding-agent-sandbox"
)


def run_in_sandbox(
    command: list[str],
    timeout: int = 30,
    read_only: bool = True
) -> dict:

    workspace = (
        get_workspace()
    )


    volume = (
        f"{workspace}:/workspace"
    )


    if read_only:

        volume += ":ro"


    docker_command = [

        "docker",

        "run",

        "--rm",

        "--network",
        "none",

        "--memory",
        "512m",

        "--cpus",
        "1",

        "-v",
        volume,

        "-w",
        "/workspace",

        SANDBOX_IMAGE,

        *command
    ]


    try:

        result = (
            subprocess.run(

                docker_command,

                capture_output=True,

                text=True,

                timeout=timeout
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


    except subprocess.TimeoutExpired:

        return {

            "success":
                False,

            "returncode":
                None,

            "stdout":
                "",

            "stderr":
                (
                    f"Sandbox执行超过"
                    f"{timeout}秒"
                )
        }


    except FileNotFoundError as e:

        return {

            "success":
                False,

            "returncode":
                None,

            "stdout":
                "",

            "stderr":
                (
                    f"Docker不可用：{e}"
                )
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
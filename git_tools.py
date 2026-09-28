import subprocess

from runtime_paths import (
    get_workspace
)


def run_git(
    args: list[str]
) -> dict:

    workspace = (
        get_workspace()
    )


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

                timeout=10
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


def git_diff() -> dict:

    return (
        run_git(
            [
                "diff"
            ]
        )
    )


def git_status() -> dict:

    return (
        run_git(
            [
                "status",
                "--short"
            ]
        )
    )
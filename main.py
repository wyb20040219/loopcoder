from agent import (
    run_agent
)


def print_banner():

    print(
        "=" * 50
    )

    print(
        "LoopCoder"
    )

    print(
        "Long-Horizon Coding Agent Runtime "
        "& Control Plane"
    )

    print(
        "=" * 50
    )

    print(
        "\n核心能力："
    )

    print(
        "- Goal / Todo State"
    )

    print(
        "- Control Tick"
    )

    print(
        "- Claim / Lease"
    )

    print(
        "- Tool Gate / Human Approval"
    )

    print(
        "- Quota"
    )

    print(
        "- Protected Paths"
    )

    print(
        "- Docker Sandbox"
    )

    print(
        "- Git Diff Review"
    )

    print(
        "- Pytest Verification"
    )

    print(
        "- Evidence-driven Acceptance"
    )

    print(
        "- Checkpoint / Resume"
    )

    print(
        "- Attention Queue"
    )

    print(
        "- Trace / Run History"
    )

    print(
        "\n输入 exit 退出。"
    )


def main():

    print_banner()


    while True:

        user_task = input(
            "\n你："
        ).strip()


        if not user_task:

            continue


        if (
            user_task.lower()
            ==
            "exit"
        ):

            print(
                "\nLoopCoder 已退出。"
            )

            break


        try:

            result = (
                run_agent(
                    user_task
                )
            )


            print(
                "\n"
                +
                "=" * 50
            )

            print(
                "LoopCoder Final Result"
            )

            print(
                "=" * 50
            )

            print(
                result
            )


        except KeyboardInterrupt:

            print(
                "\n\n任务被用户中断。"
            )


        except Exception as e:

            print(
                "\nLoopCoder运行失败："
            )

            print(
                f"{type(e).__name__}: {e}"
            )


if __name__ == "__main__":

    main()